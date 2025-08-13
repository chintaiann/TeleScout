"""Web GUI interface for TeleScout."""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import yaml
import os
import secrets
import threading
import webbrowser
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from .telegram_client import TeleScoutClient
from .config import load_config


class TeleScoutGUI:
    """Web-based GUI for TeleScout."""
    
    def __init__(self, config_path="config.yaml"):
        self.app = Flask(__name__, template_folder='../templates', static_folder='../static')
        self.app.secret_key = secrets.token_hex(32)
        self.config_path = config_path
        self.config_data: Optional[Dict[str, Any]] = None
        
        # Monitoring state
        self.monitoring_status = 'stopped'
        self.client: Optional[TeleScoutClient] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
        self.messages_found = 0
        
        self.setup_routes()
        self.load_config_data()
    
    def setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/')
        def index():
            return redirect(url_for('home'))
        
        @self.app.route('/home')
        def home():
            """Home/Dashboard page."""
            return render_template('home.html')
        
        @self.app.route('/config')
        def config():
            """Configuration page."""
            return render_template('config.html', config=self.config_data or {})
        
        @self.app.route('/monitoring')
        def monitoring():
            """Monitoring page."""
            return render_template('monitoring.html')
        
        @self.app.route('/keywords')
        def keywords():
            """Keywords management page."""
            keywords_list = self.config_data.get('keywords', []) if self.config_data else []
            return render_template('keywords.html', keywords=keywords_list)
        
        @self.app.route('/channels')
        def channels():
            """Channels management page."""
            channels_list = self.config_data.get('channels', []) if self.config_data else []
            return render_template('channels.html', channels=channels_list)
        
        @self.app.route('/logs')
        def logs():
            """Logs viewer page."""
            return render_template('logs.html')
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            """API endpoint for configuration management."""
            if request.method == 'GET':
                return jsonify(self.config_data or {})
            
            elif request.method == 'POST':
                try:
                    config_data = request.json
                    
                    # Validate required fields
                    required_fields = ['telegram', 'forward_to_user_id']
                    for field in required_fields:
                        if field not in config_data:
                            return jsonify({'error': f'Missing required field: {field}'}), 400
                    
                    # Save to file
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config_data, f, default_flow_style=False, indent=2)
                    
                    self.config_data = config_data
                    return jsonify({'message': 'Configuration saved successfully'})
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/keywords', methods=['GET', 'POST', 'DELETE'])
        def api_keywords():
            """API endpoint for keywords management."""
            if not self.config_data:
                return jsonify({'error': 'No configuration loaded'}), 400
            
            if request.method == 'GET':
                return jsonify(self.config_data.get('keywords', []))
            
            elif request.method == 'POST':
                keyword = request.json.get('keyword', '').strip()
                if keyword:
                    if 'keywords' not in self.config_data:
                        self.config_data['keywords'] = []
                    if keyword.lower() not in [k.lower() for k in self.config_data['keywords']]:
                        self.config_data['keywords'].append(keyword.lower())
                        self.save_config()
                        return jsonify({'message': 'Keyword added successfully'})
                    else:
                        return jsonify({'error': 'Keyword already exists'}), 400
                return jsonify({'error': 'Invalid keyword'}), 400
            
            elif request.method == 'DELETE':
                keyword = request.json.get('keyword', '').strip()
                if keyword and 'keywords' in self.config_data:
                    try:
                        self.config_data['keywords'].remove(keyword.lower())
                        self.save_config()
                        return jsonify({'message': 'Keyword removed successfully'})
                    except ValueError:
                        return jsonify({'error': 'Keyword not found'}), 404
                return jsonify({'error': 'Invalid keyword'}), 400
        
        @self.app.route('/api/channels', methods=['GET', 'POST', 'DELETE'])
        def api_channels():
            """API endpoint for channels management."""
            if not self.config_data:
                return jsonify({'error': 'No configuration loaded'}), 400
            
            if request.method == 'GET':
                return jsonify(self.config_data.get('channels', []))
            
            elif request.method == 'POST':
                channel = request.json.get('channel', '').strip()
                if channel:
                    if 'channels' not in self.config_data:
                        self.config_data['channels'] = []
                    if channel not in self.config_data['channels']:
                        self.config_data['channels'].append(channel)
                        self.save_config()
                        return jsonify({'message': 'Channel added successfully'})
                    else:
                        return jsonify({'error': 'Channel already exists'}), 400
                return jsonify({'error': 'Invalid channel'}), 400
            
            elif request.method == 'DELETE':
                channel = request.json.get('channel', '').strip()
                if channel and 'channels' in self.config_data:
                    try:
                        self.config_data['channels'].remove(channel)
                        self.save_config()
                        return jsonify({'message': 'Channel removed successfully'})
                    except ValueError:
                        return jsonify({'error': 'Channel not found'}), 404
                return jsonify({'error': 'Invalid channel'}), 400
        
        @self.app.route('/api/monitoring/status', methods=['GET'])
        def api_monitoring_status():
            """Get current monitoring status."""
            channels_count = len(self.config_data.get('channels', [])) if self.config_data else 0
            keywords_count = len(self.config_data.get('keywords', [])) if self.config_data else 0
            
            # Convert start_time to milliseconds for JavaScript
            start_time_ms = int(self.start_time * 1000) if self.start_time else None
            
            return jsonify({
                'status': self.monitoring_status,
                'start_time': start_time_ms,
                'channels_count': channels_count,
                'keywords_count': keywords_count,
                'messages_found': self.messages_found
            })
        
        @self.app.route('/api/monitoring/start', methods=['POST'])
        def api_monitoring_start():
            """Start monitoring."""
            if self.monitoring_status == 'running':
                return jsonify({'error': 'Monitoring is already running'}), 400
            
            try:
                # Load current config
                config = load_config(self.config_path)
                
                # Validate configuration
                if not config.channels:
                    return jsonify({'error': 'No channels configured. Please add channels first.'}), 400
                if not config.keywords:
                    return jsonify({'error': 'No keywords configured. Please add keywords first.'}), 400
                
                # Start monitoring in background thread
                self.monitoring_thread = threading.Thread(target=self._start_monitoring_async, args=(config,))
                self.monitoring_thread.daemon = True
                self.monitoring_thread.start()
                
                self.monitoring_status = 'starting'
                return jsonify({'message': 'Monitoring is starting...'})
                
            except Exception as e:
                return jsonify({'error': f'Failed to start monitoring: {str(e)}'}), 500
        
        @self.app.route('/api/monitoring/scan', methods=['POST'])
        def api_monitoring_scan():
            """Start scan-only mode."""
            if self.monitoring_status in ['running', 'scanning']:
                return jsonify({'error': 'Monitoring or scanning is already in progress'}), 400
            
            try:
                # Load current config
                config = load_config(self.config_path)
                
                # Validate configuration
                if not config.channels:
                    return jsonify({'error': 'No channels configured. Please add channels first.'}), 400
                if not config.keywords:
                    return jsonify({'error': 'No keywords configured. Please add keywords first.'}), 400
                if not config.time_window_hours:
                    return jsonify({'error': 'Time window must be configured for historical scanning.'}), 400
                
                # Start scan in background thread
                self.monitoring_thread = threading.Thread(target=self._start_scan_only_async, args=(config,))
                self.monitoring_thread.daemon = True
                self.monitoring_thread.start()
                
                self.monitoring_status = 'scanning'
                return jsonify({'message': 'Historical scan is starting...'})
                
            except Exception as e:
                return jsonify({'error': f'Failed to start scan: {str(e)}'}), 500
        
        @self.app.route('/api/monitoring/realtime', methods=['POST'])
        def api_monitoring_realtime():
            """Start real-time monitoring only (no historical scan)."""
            if self.monitoring_status in ['running', 'scanning']:
                return jsonify({'error': 'Monitoring or scanning is already in progress'}), 400
            
            try:
                # Load current config
                config = load_config(self.config_path)
                
                # Validate configuration
                if not config.channels:
                    return jsonify({'error': 'No channels configured. Please add channels first.'}), 400
                if not config.keywords:
                    return jsonify({'error': 'No keywords configured. Please add keywords first.'}), 400
                
                # Start real-time monitoring in background thread
                self.monitoring_thread = threading.Thread(target=self._start_realtime_async, args=(config,))
                self.monitoring_thread.daemon = True
                self.monitoring_thread.start()
                
                self.monitoring_status = 'running'
                return jsonify({'message': 'Real-time monitoring is starting...'})
                
            except Exception as e:
                return jsonify({'error': f'Failed to start real-time monitoring: {str(e)}'}), 500
        
        @self.app.route('/api/monitoring/stop', methods=['POST'])
        def api_monitoring_stop():
            """Stop monitoring."""
            if self.monitoring_status == 'stopped':
                return jsonify({'error': 'Monitoring is already stopped'}), 400
            
            try:
                self.monitoring_status = 'stopping'
                
                if self.client:
                    # Stop the client in a separate thread to avoid blocking
                    def stop_client():
                        try:
                            asyncio.run(self.client.stop())
                        except Exception as e:
                            print(f"Error stopping client: {e}")
                        finally:
                            self.monitoring_status = 'stopped'
                            self.client = None
                            self.start_time = None
                    
                    stop_thread = threading.Thread(target=stop_client)
                    stop_thread.daemon = True
                    stop_thread.start()
                else:
                    self.monitoring_status = 'stopped'
                
                return jsonify({'message': 'Monitoring is stopping...'})
                
            except Exception as e:
                self.monitoring_status = 'stopped'
                return jsonify({'error': f'Failed to stop monitoring: {str(e)}'}), 500
    
    def load_config_data(self):
        """Load configuration data from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f)
            else:
                self.config_data = {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config_data = {}
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _start_monitoring_async(self, config):
        """Start monitoring in async context (runs in background thread)."""
        try:
            asyncio.run(self._run_monitoring(config))
        except Exception as e:
            print(f"Monitoring error: {e}")
            self.monitoring_status = 'stopped'
            self.client = None
            self.start_time = None
    
    def _start_scan_only_async(self, config):
        """Start scan-only in async context (runs in background thread)."""
        try:
            asyncio.run(self._run_scan_only(config))
        except Exception as e:
            print(f"Scan error: {e}")
            self.monitoring_status = 'stopped'
            self.client = None
            self.start_time = None
    
    def _start_realtime_async(self, config):
        """Start real-time monitoring in async context (runs in background thread)."""
        try:
            asyncio.run(self._run_realtime_only(config))
        except Exception as e:
            print(f"Real-time monitoring error: {e}")
            self.monitoring_status = 'stopped'
            self.client = None
            self.start_time = None
    
    async def _run_monitoring(self, config):
        """Run the monitoring process."""
        try:
            self.client = TeleScoutClient(config)
            # Set up callback to update message count
            self.client.on_message_forwarded = self._on_message_forwarded
            await self.client.start()
            
            self.monitoring_status = 'running'
            self.start_time = time.time()
            self.messages_found = 0
            
            print("TeleScout monitoring started from GUI")
            
            # Run historical scan if configured
            if config.time_window_hours:
                print("Starting historical scan...")
                await self.client.scan_historical_messages()
            
            # Start real-time monitoring
            print("Starting real-time monitoring...")
            await self.client.start_monitoring()
            
        except Exception as e:
            print(f"Error in monitoring: {e}")
            self.monitoring_status = 'stopped'
            if self.client:
                try:
                    await self.client.stop()
                except:
                    pass
                self.client = None
            self.start_time = None
    
    async def _run_scan_only(self, config):
        """Run historical scan only (no real-time monitoring)."""
        try:
            self.client = TeleScoutClient(config)
            # Set up callback to update message count
            self.client.on_message_forwarded = self._on_message_forwarded
            await self.client.start()
            
            self.monitoring_status = 'scanning'
            self.start_time = time.time()
            self.messages_found = 0
            
            print("TeleScout historical scan started from GUI")
            
            # Run historical scan only
            if config.time_window_hours:
                await self.client.scan_historical_messages()
                print("Historical scan completed")
            else:
                print("No time window configured, scan completed immediately")
            
            # Stop client after scan
            await self.client.stop()
            
            # Update status
            self.monitoring_status = 'stopped'
            self.client = None
            print("Scan-only mode completed")
            
        except Exception as e:
            print(f"Error in scan-only mode: {e}")
            self.monitoring_status = 'stopped'
            if self.client:
                try:
                    await self.client.stop()
                except:
                    pass
                self.client = None
            self.start_time = None
    
    async def _run_realtime_only(self, config):
        """Run real-time monitoring only (no historical scan)."""
        try:
            self.client = TeleScoutClient(config)
            # Set up callback to update message count
            self.client.on_message_forwarded = self._on_message_forwarded
            await self.client.start()
            
            self.monitoring_status = 'running'
            self.start_time = time.time()
            self.messages_found = 0
            
            print("TeleScout real-time monitoring started from GUI (skipping historical scan)")
            
            # Start real-time monitoring only (skip historical scan)
            await self.client.start_monitoring()
            
        except Exception as e:
            print(f"Error in real-time monitoring: {e}")
            self.monitoring_status = 'stopped'
            if self.client:
                try:
                    await self.client.stop()
                except:
                    pass
                self.client = None
            self.start_time = None
    
    def _on_message_forwarded(self):
        """Callback function called when a message is forwarded."""
        self.messages_found += 1
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the Flask app."""
        self.app.run(host=host, port=port, debug=debug)


def launch_gui(config_path="config.yaml", host='127.0.0.1', port=5000):
    """Launch the TeleScout web GUI."""
    gui = TeleScoutGUI(config_path)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f'http://{host}:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print(f"Starting TeleScout GUI at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        gui.run(host=host, port=port)
    except KeyboardInterrupt:
        print("\nShutting down TeleScout GUI...")
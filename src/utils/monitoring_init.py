"""Monitoring system initialization script.

This script initializes all enhanced monitoring components and can be
run at system startup or manually to activate enhanced monitoring.
"""

import logging
import sys
import time
from pathlib import Path

logging.Formatter.converter = time.gmtime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.monitoring import (
    shadow_collector, 
    security_monitor, 
    performance_monitor,
    enhanced_logger,
    AlertSystem
)

logger = logging.getLogger(__name__)


def initialize_monitoring(kb_base: str = "knowledge_base"):
    """Initialize all monitoring components."""
    
    logger.info("Initializing enhanced monitoring system...")
    
    # Initialize alert system
    alert_system = AlertSystem(kb_base)
    alert_system.log_alert(
        "INFO", 
        "MONITORING_INIT", 
        "Enhanced monitoring system starting up"
    )
    
    # Start shadow data collection
    try:
        shadow_collector.start_collection()
        logger.info("Shadow data collection started")
    except Exception as e:
        logger.error(f"Failed to start shadow data collection: {e}")
    
    # Log system startup
    enhanced_logger.log_component_start(
        component="MONITORING_SYSTEM",
        version="1.0",
        config={
            "shadow_collection": True,
            "security_monitoring": True,
            "performance_monitoring": True,
            "kb_base": kb_base
        }
    )
    
    # Create initial system snapshot
    snapshot_id = enhanced_logger.create_session_snapshot()
    logger.info(f"Created initial system snapshot: {snapshot_id}")
    
    # Test all components
    test_results = test_monitoring_components()
    
    # Log startup summary
    alert_system.log_alert(
        "INFO",
        "MONITORING_READY", 
        "Enhanced monitoring system initialized successfully",
        {"test_results": test_results, "snapshot_id": snapshot_id}
    )
    
    logger.info("Enhanced monitoring system ready")
    return True


def test_monitoring_components():
    """Test all monitoring components and return results."""
    results = {}
    
    # Test shadow collector
    try:
        shadow_collector.collect_metric("test", 1.0, "INIT_TEST")
        results["shadow_collector"] = "OK"
    except Exception as e:
        results["shadow_collector"] = f"ERROR: {e}"
        logger.error(f"Shadow collector test failed: {e}")
    
    # Test security monitor
    try:
        security_monitor.log_data_access("TEST", "test_resource", "system", "READ")
        results["security_monitor"] = "OK"
    except Exception as e:
        results["security_monitor"] = f"ERROR: {e}"
        logger.error(f"Security monitor test failed: {e}")
    
    # Test performance monitor
    try:
        with performance_monitor.time_operation("INIT_TEST", "component_test"):
            pass  # Timed operation
        results["performance_monitor"] = "OK"
    except Exception as e:
        results["performance_monitor"] = f"ERROR: {e}"
        logger.error(f"Performance monitor test failed: {e}")
    
    # Test enhanced logger
    try:
        enhanced_logger.log_component_start("TEST_COMPONENT", "1.0")
        enhanced_logger.log_component_stop("TEST_COMPONENT", 0, "test complete")
        results["enhanced_logger"] = "OK"
    except Exception as e:
        results["enhanced_logger"] = f"ERROR: {e}"
        logger.error(f"Enhanced logger test failed: {e}")
    
    return results


def shutdown_monitoring():
    """Gracefully shutdown monitoring components."""
    
    logger.info("Shutting down enhanced monitoring system...")
    
    # Stop shadow data collection
    try:
        shadow_collector.stop_collection()
        logger.info("Shadow data collection stopped")
    except Exception as e:
        logger.error(f"Error stopping shadow data collection: {e}")
    
    # Log shutdown
    enhanced_logger.log_component_stop(
        component="MONITORING_SYSTEM",
        exit_code=0,
        reason="Normal shutdown"
    )
    
    # Create final snapshot
    try:
        snapshot_id = enhanced_logger.create_session_snapshot()
        logger.info(f"Created shutdown snapshot: {snapshot_id}")
    except Exception as e:
        logger.error(f"Failed to create shutdown snapshot: {e}")
    
    logger.info("Enhanced monitoring system shutdown complete")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description='Enhanced monitoring system control')
    parser.add_argument('action', choices=['start', 'stop', 'test'], 
                       help='Action to perform')
    parser.add_argument('--kb-base', default='knowledge_base',
                       help='Knowledge base directory')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'start':
            success = initialize_monitoring(args.kb_base)
            sys.exit(0 if success else 1)
        elif args.action == 'stop':
            shutdown_monitoring()
            sys.exit(0)
        elif args.action == 'test':
            results = test_monitoring_components()
            for component, result in results.items():
                print(f"{component}: {result}")
            
            all_ok = all("OK" in result for result in results.values())
            sys.exit(0 if all_ok else 1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        shutdown_monitoring()
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

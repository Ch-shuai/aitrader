"""
统一日志系统 - 记录所有操作、执行结果和时间戳
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps
import inspect

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
OPERATION_LOG = LOG_DIR / "operations.log"
ERROR_LOG = LOG_DIR / "errors.log"
BACKTEST_LOG = LOG_DIR / "backtest.log"
STRATEGY_LOG = LOG_DIR / "strategy.log"
DATA_LOG = LOG_DIR / "data_sync.log"
ML_LOG = LOG_DIR / "ml.log"


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # 添加额外字段
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        if hasattr(record, "entity_type"):
            log_entry["entity_type"] = record.entity_type
        if hasattr(record, "entity_id"):
            log_entry["entity_id"] = record.entity_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "result"):
            log_entry["result"] = record.result
        if hasattr(record, "params"):
            log_entry["params"] = record.params
        if hasattr(record, "user"):
            log_entry["user"] = record.user

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class OperationLogger:
    """操作日志记录器"""

    def __init__(self, name: str, log_file: Path):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not self.logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(StructuredLogFormatter())
            self.logger.addHandler(file_handler)

            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console_handler)

    def log_operation(
        self,
        operation: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        params: Optional[Dict] = None,
        result: Optional[Any] = None,
        duration_ms: Optional[float] = None,
        level: str = "INFO"
    ):
        """记录操作日志"""
        extra = {
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "params": params,
            "result": result,
            "duration_ms": duration_ms
        }

        if level == "ERROR":
            self.logger.error(operation, extra=extra)
        elif level == "WARNING":
            self.logger.warning(operation, extra=extra)
        else:
            self.logger.info(operation, extra=extra)


# 创建专用日志记录器
operation_logger = OperationLogger("aitrader.operation", OPERATION_LOG)
error_logger = OperationLogger("aitrader.error", ERROR_LOG)
backtest_logger = OperationLogger("aitrader.backtest", BACKTEST_LOG)
strategy_logger = OperationLogger("aitrader.strategy", STRATEGY_LOG)
data_logger = OperationLogger("aitrader.data", DATA_LOG)
ml_logger = OperationLogger("aitrader.ml", ML_LOG)


def log_operation(operation_name: str, entity_type: Optional[str] = None):
    """装饰器：自动记录函数调用"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()

            # 获取函数参数信息
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 过滤掉self和db参数
            params = {
                k: str(v)[:100] if not isinstance(v, (int, float, bool, str)) else v
                for k, v in bound_args.arguments.items()
                if k not in ('self', 'db', 'session')
            }

            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                # 简化结果
                result_summary = None
                if isinstance(result, dict):
                    if "error" in result:
                        result_summary = {"status": "error", "message": result["error"]}
                    else:
                        result_summary = {"status": "success", "keys": list(result.keys())}

                operation_logger.log_operation(
                    operation=operation_name,
                    entity_type=entity_type,
                    params=params,
                    result=result_summary,
                    duration_ms=round(duration, 2)
                )

                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                error_logger.log_operation(
                    operation=f"{operation_name}_error",
                    entity_type=entity_type,
                    params=params,
                    result={"error": str(e)},
                    duration_ms=round(duration, 2),
                    level="ERROR"
                )
                raise

        return wrapper
    return decorator


def log_data_sync(operation: str, details: Dict[str, Any]):
    """记录数据同步日志"""
    data_logger.log_operation(
        operation=operation,
        entity_type="data_sync",
        params=details
    )


def log_strategy_execution(strategy_id: int, strategy_name: str, signals_count: int, **kwargs):
    """记录策略执行日志"""
    strategy_logger.log_operation(
        operation="strategy_execute",
        entity_type="strategy",
        entity_id=str(strategy_id),
        params={"name": strategy_name, "signals_generated": signals_count, **kwargs}
    )


def log_backtest_result(backtest_id: int, strategy_name: str, metrics: Dict[str, Any]):
    """记录回测结果日志"""
    backtest_logger.log_operation(
        operation="backtest_complete",
        entity_type="backtest",
        entity_id=str(backtest_id),
        params={"strategy": strategy_name},
        result=metrics
    )


def log_ml_training(code: str, model_type: str, metrics: Dict[str, Any]):
    """记录ML训练日志"""
    ml_logger.log_operation(
        operation="model_training",
        entity_type="ml_model",
        entity_id=code,
        params={"model_type": model_type},
        result=metrics
    )


class LogReader:
    """日志读取器 - 用于查询历史日志"""

    @staticmethod
    def read_logs(log_type: str = "operation", limit: int = 100) -> list:
        """读取日志文件"""
        log_files = {
            "operation": OPERATION_LOG,
            "error": ERROR_LOG,
            "backtest": BACKTEST_LOG,
            "strategy": STRATEGY_LOG,
            "data": DATA_LOG,
            "ml": ML_LOG
        }

        log_file = log_files.get(log_type, OPERATION_LOG)

        if not log_file.exists():
            return []

        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f.readlines()[-limit:]:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        return logs

    @staticmethod
    def get_recent_operations(hours: int = 24) -> list:
        """获取最近的操作日志"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        logs = LogReader.read_logs("operation", limit=1000)

        recent_logs = []
        for log in logs:
            try:
                log_time = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
                if log_time.timestamp() > cutoff:
                    recent_logs.append(log)
            except:
                continue

        return recent_logs

    @staticmethod
    def get_system_stats() -> dict:
        """获取系统统计信息"""
        stats = {
            "total_operations": 0,
            "total_errors": 0,
            "recent_backtests": 0,
            "recent_trains": 0
        }

        # 统计操作数
        if OPERATION_LOG.exists():
            with open(OPERATION_LOG) as f:
                stats["total_operations"] = sum(1 for _ in f)

        # 统计错误数
        if ERROR_LOG.exists():
            with open(ERROR_LOG) as f:
                stats["total_errors"] = sum(1 for _ in f)

        # 统计最近24小时的回测
        cutoff = datetime.utcnow().timestamp() - 86400
        if BACKTEST_LOG.exists():
            with open(BACKTEST_LOG) as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        log_time = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
                        if log_time.timestamp() > cutoff:
                            stats["recent_backtests"] += 1
                    except:
                        continue

        return stats


# 初始化日志
def init_logging():
    """初始化日志系统"""
    # 创建必要的日志文件
    for log_file in [OPERATION_LOG, ERROR_LOG, BACKTEST_LOG, STRATEGY_LOG, DATA_LOG, ML_LOG]:
        if not log_file.exists():
            log_file.touch()

    operation_logger.log_operation(
        operation="system_startup",
        entity_type="system",
        result={"status": "logging_initialized"}
    )


if __name__ == "__main__":
    # 测试日志系统
    init_logging()

    operation_logger.log_operation(
        operation="test",
        entity_type="test",
        params={"foo": "bar"},
        result={"success": True}
    )

    print("日志系统测试完成")
    print(f"日志目录: {LOG_DIR}")

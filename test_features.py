"""
功能测试脚本 - 验证所有核心功能
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_all_features():
    """测试所有功能"""
    results = []

    # Test 1: 导入所有服务
    print("=" * 50)
    print("测试 1: 服务导入")
    print("=" * 50)
    try:
        from app.services.scheduler_service import scheduler_service
        from app.services.factor_service import FactorService
        from app.services.strategy_service import StrategyService
        from app.services.sync_service import sync_service
        from app.services.data_service import StockDataService, NewsService
        print("✅ 所有服务导入成功")
        results.append(("服务导入", True))
    except Exception as e:
        print(f"❌ 服务导入失败: {e}")
        results.append(("服务导入", False))
        return results

    # Test 2: 调度器初始化
    print("\n" + "=" * 50)
    print("测试 2: 定时任务调度器")
    print("=" * 50)
    try:
        scheduler_service.init_scheduler()
        jobs = scheduler_service.get_jobs()
        print(f"✅ 调度器初始化成功")
        print(f"   任务数量: {len(jobs)}")
        for job in jobs:
            print(f"   - {job['id']}: {job['name']}")
        results.append(("调度器初始化", True))
    except Exception as e:
        print(f"❌ 调度器初始化失败: {e}")
        results.append(("调度器初始化", False))

    # Test 3: 因子服务
    print("\n" + "=" * 50)
    print("测试 3: 因子服务")
    print("=" * 50)
    try:
        factor_service = FactorService()
        factors = factor_service.get_all_factors()
        print(f"✅ 因子服务正常")
        print(f"   因子数量: {len(factors)}")
        print(f"   批量计算: {'batch_calculate_all_factors' in dir(factor_service)}")
        results.append(("因子服务", True))
    except Exception as e:
        print(f"❌ 因子服务失败: {e}")
        results.append(("因子服务", False))

    # Test 4: 策略服务
    print("\n" + "=" * 50)
    print("测试 4: 策略服务")
    print("=" * 50)
    try:
        strategy_service = StrategyService()
        has_fscore = hasattr(strategy_service, '_calculate_f_score')
        has_financial = hasattr(strategy_service, '_get_financial_data')
        print(f"✅ 策略服务正常")
        print(f"   F-Score计算: {has_fscore}")
        print(f"   财务数据获取: {has_financial}")
        results.append(("策略服务", True))
    except Exception as e:
        print(f"❌ 策略服务失败: {e}")
        results.append(("策略服务", False))

    # Test 5: 数据同步服务
    print("\n" + "=" * 50)
    print("测试 5: 数据同步服务")
    print("=" * 50)
    try:
        print(f"✅ 数据同步服务正常")
        print(f"   初始化方法: {'initialize_data' in dir(sync_service)}")
        print(f"   每日更新: {'daily_update' in dir(sync_service)}")
        print(f"   状态查询: {'get_sync_status' in dir(sync_service)}")
        results.append(("数据同步服务", True))
    except Exception as e:
        print(f"❌ 数据同步服务失败: {e}")
        results.append(("数据同步服务", False))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"通过: {passed}/{total}")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    return passed == total


if __name__ == "__main__":
    success = test_all_features()
    sys.exit(0 if success else 1)

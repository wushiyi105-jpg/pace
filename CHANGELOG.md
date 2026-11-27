# 更新记录

## Unreleased

- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 五区间配速表
- 周量增幅 10% 校验
- 连续两周低完成率重排
- 赛前长距离 70% 校验
- ICS 导出

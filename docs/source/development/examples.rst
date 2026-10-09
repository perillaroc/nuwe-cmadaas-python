示例
====

现有 MUSIC 原生示例位于仓库的 ``example/`` 目录。
地面站点高层示例已位于 ``examples/high_level/station.py``，从仓库根目录运行：

.. code-block:: bash

   uv run python -m examples.high_level.station

脚本默认使用合成数据，无需账号，包含筛选、latest 时次表、数值转换及结果断言。
:doc:`地面站点指南 <../guide/high-level/obs/station>` 复用同一客户端准备和结果校验。
完整的高层/MUSIC 示例集及旧包迁移索引将在 D20 整合。

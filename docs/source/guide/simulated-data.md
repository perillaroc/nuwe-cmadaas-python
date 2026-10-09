# 模拟数据与客户端注入

指南中的模拟示例使用人工构造的响应，无需 CMADaaS 账号。示例中的 `FAKE001`、`FAKE002` 等站号和固定日期均为虚构内容，不能用于真实服务查询。

高层示例通过公开函数的 `client=` 参数注入 `examples._support.FakeClient`；底层示例使用注入合成 transport 的真实 `CMADaaSClient`。辅助源码位于仓库的 `examples/_support/`，不属于安装后的 `nuwe_cmadaas` 公共 API。下载示例使用 `.invalid` 地址和人工字节内容；未登记的请求会立即失败。

普通教程会折叠数据准备单元。点击代码单元旁的展开按钮即可查看完整的响应构造和注入过程；折叠只影响显示，不影响执行。所有教程页面独立准备客户端，不依赖前一页的内核状态。

完整的模拟机制、源码获取方式及真实客户端切换说明将在本章继续补充。现在可参阅仓库中的 `examples/_support/README.md` 和 `docs/README.md`。

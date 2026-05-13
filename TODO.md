# Enikk TODO

## 进行中

- [x] ui_parser: OCR + YOLO 并行执行（ThreadPoolExecutor）~40% 延迟降低
- [x] agent: 新增 read_image 多模态工具
- [x] agent: click 工具增加 target + reason 字段（可追溯）
- [x] agent: 截图目录自动清理（上限 1024 文件）

## 待规划

### 📋 Web Dashboard（嵌入式 SPA）

**状态**：✅ 后端完成，✅ 前端骨架完成，待联调

**已完成**：
- [x] ws_server.py: WebSocket JSON-RPC 服务器
- [x] agent/manager.py: AgentManager 生命周期管理（start/abort/history）
- [x] agent/hermes_tools.py: InternalToolContext（直接调 daemon，不走 HTTP）
- [x] daemon.py: 整合 AgentManager + WsServer
- [x] cli.py: ws-daemon 命令
- [x] config.py: ws_port 字段
- [x] frontend/: Vue 3 + Vite + TS + Naive UI 脚手架
- [x] frontend/ws-client.ts: WebSocket JSON-RPC 客户端
- [x] frontend/stores/chat.ts: Pinia 聊天状态管理
- [x] frontend/components/ChatPanel.vue: 聊天界面（消息列表 + 输入框 + 中断按钮）
- [x] Build 通过（229KB gzipped）

**待做**：
- [ ] 集成 FastAPI 静态文件服务（build 产物）
- [ ] 联调测试（ws-daemon + 前端）
- [ ] session.history 集成
- [ ] 截图预览功能

### 🔍 OmniParser UI 增强

**状态**：已对比分析，待启动

**发现**：
- Enikk ui_parser.py 已有 YOLO + OCR 管线
- 缺少图标功能描述模块（OmniParser 用 BLIP-2/Florence-2）
- SoM 标注可视化未实现

**待做**：
- [ ] 加图标描述模型（BLIP-2 或 Florence-2）
- [ ] render_som() 方法：在截图上叠加 BBox + ID 标注
- [ ] screenshot-debug CLI 命令
- [ ] /api/screenshot/debug 端点

### 📦 其他

- [ ] 考虑用 RT-DETR (Apache 2.0) 替代 YOLOv8 (AGPL)（如需商业友好）
- [ ] 游戏专用 UI 数据集采集 + YOLO 微调

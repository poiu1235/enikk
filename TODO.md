# Enikk TODO

## 进行中

- [x] ui_parser: OCR + YOLO 并行执行（ThreadPoolExecutor）~40% 延迟降低
- [x] agent: 新增 read_image 多模态工具
- [x] agent: click 工具增加 target + reason 字段（可追溯）
- [x] agent: 截图目录自动清理（上限 1024 文件）

## 待规划

### 📋 Web Dashboard（嵌入式 SPA）

**状态**：已决定技术栈，待启动

**技术选型**：
- 前端：Vue 3 SFC + Vite + TypeScript
- 组件库：Naive UI（轻量、TS 原生）
- 状态管理：Pinia
- 后端：FastAPI（复用 Enikk server）
- 通信：WebSocket JSON-RPC（参考 OpenClaw Control UI 架构）

**目标**：
- 替代 Hermes Dashboard 的 PTY hack 方案
- 原生 Web Chat UI（非终端模拟器）
- 嵌入 FastAPI 静态文件服务
- 支持聊天、配置、会话历史

**架构参考**：
- OpenClaw Control UI：Vite + Lit，WebSocket JSON-RPC，单一端口
- 改进：Vue SFC 替代 Lit（coding agent 更友好、组件生态丰富）

**下一步**：
1. 搭脚手架（Vue 3 + Vite + TS）
2. WebSocket JSON-RPC 客户端
3. 聊天界面骨架（消息列表 + 输入框）
4. FastAPI WS 端点
5. session.history 集成

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

# NAGA 开发环境搭建指南

## 前置要求

- Python 3.9+
- Node.js 18+
- npm 或 yarn

## 后端启动

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# 编辑 .env 文件填入 API Keys
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

访问 http://localhost:8080/docs 查看 API 文档

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 验证

1. 后端能访问 http://localhost:8080/docs
2. 前端能访问 http://localhost:5173
3. 前端能调用后端 API（检查浏览器控制台无 CORS 错误）
# WxMpCatcher 授权服务器

## 启动

```bash
cd server
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 环境变量（生产环境务必修改）
set WXMP_ADMIN_TOKEN=your-secret-admin-token
set WXMP_LICENSE_DB=data\license.db

uvicorn app.main:app --host 0.0.0.0 --port 8787
```

## 生成激活码

```bash
python scripts/generate_codes.py -n 10 --token your-secret-admin-token
```

## API

| 接口 | 说明 |
|------|------|
| `POST /api/v1/trial/status` | 查询设备试用状态 |
| `POST /api/v1/trial/report` | 上报试用抓取数量 |
| `POST /api/v1/activate` | 激活（一码一机） |
| `POST /api/v1/validate` | 校验授权 |
| `POST /admin/generate-codes?admin_token=...` | 批量生成激活码 |

## 客户端配置

安装包或环境变量指定授权服务器：

```bat
set WXMP_LICENSE_URL=https://your-domain.com
set WXMP_PURCHASE_URL=https://your-shop.com/buy
```

或在软件「设置 → 授权服务器」中填写。

## 部署建议

- 使用 HTTPS（Nginx 反代 + Let's Encrypt）
- 修改 `WXMP_ADMIN_TOKEN`
- 定期备份 `data/license.db`

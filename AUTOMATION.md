# Google Scholar 自动更新

`.github/workflows/update-scholar.yml` 每天北京时间 09:17 运行，也可以在
GitHub 仓库的 **Actions → Update Google Scholar metrics → Run workflow** 手动运行。

工作流会：

1. 读取 Google Scholar 公开主页中的总引用次数和 H 指数；
2. 拒绝异常数据以及引用次数或 H 指数倒退；
3. 更新 `index.html`、`zh.html`、`data/scholar_metrics.json` 和简历 LaTeX；
4. 使用 XeLaTeX 重新生成 `files/ShuangLi.pdf`；
5. 自动提交变化并部署 GitHub Pages。

## GitHub 一次性设置

1. 在仓库 **Settings → Pages → Build and deployment → Source** 中选择
   **GitHub Actions**。
2. 在 **Settings → Actions → General → Workflow permissions** 中允许工作流写入
   仓库；工作流自身只申请 `contents: write`、`pages: write` 和 `id-token: write`。
3. 注册 SerpApi 免费账户并复制 API Key。在仓库 **Settings → Secrets and
   variables → Actions → New repository secret** 中创建名为 `SERPAPI_API_KEY` 的
   Secret，并粘贴该 Key。每天运行一次只需要约 31 次请求/月。

脚本在本地网络仍可直接读取 Scholar；GitHub Runner 使用 `SERPAPI_API_KEY`，避免数据
中心 IP 被 Google 拦截。若请求失败或返回不可解析的数据，工作流会失败并保留上一次
的正确数据，不会覆盖主页或简历。

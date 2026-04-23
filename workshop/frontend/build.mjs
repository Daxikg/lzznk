import { build } from 'vite';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  try {
    console.log('Starting build...');

    const result = await build({
      build: {
        write: false,
      }
    });

    console.log('Build completed, writing files...');

    const staticDir = path.resolve(__dirname, '../static');

    // 清空静态目录中的构建文件
    const indexHtml = path.join(staticDir, 'index.html');
    const assetsDir = path.join(staticDir, 'assets');

    if (fs.existsSync(indexHtml)) fs.unlinkSync(indexHtml);
    if (fs.existsSync(assetsDir)) fs.rmSync(assetsDir, { recursive: true });
    fs.mkdirSync(assetsDir, { recursive: true });

    // 写入输出文件
    if (Array.isArray(result)) {
      result.forEach(bundle => {
        for (const output of bundle.output) {
          const filePath = path.join(staticDir, output.fileName);
          const dir = path.dirname(filePath);
          if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

          if (output.type === 'asset') {
            fs.writeFileSync(filePath, output.source);
          } else {
            fs.writeFileSync(filePath, output.code);
          }
          console.log('Written:', output.fileName);
        }
      });
    } else {
      for (const output of result.output) {
        const filePath = path.join(staticDir, output.fileName);
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

        if (output.type === 'asset') {
          fs.writeFileSync(filePath, output.source);
        } else {
          fs.writeFileSync(filePath, output.code);
        }
        console.log('Written:', output.fileName);
      }
    }

    console.log('All files written successfully!');

    // 更新 Django 模板
    const jsFile = result.output.find(o => o.fileName.endsWith('.js'))?.fileName;
    const cssFile = result.output.find(o => o.fileName.endsWith('.css'))?.fileName;

    if (jsFile && cssFile) {
      const templatePath = path.resolve(__dirname, '../templates/workshop/screen.html');
      const templateContent = `{% load static %}
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/workshop/static/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>轮轴库设备运行状态监控</title>
    <script type="module" crossorigin src="/workshop/static/${jsFile}"></script>
    <link rel="stylesheet" crossorigin href="/workshop/static/${cssFile}">
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>`;

      fs.writeFileSync(templatePath, templateContent);
      console.log('Template updated:', templatePath);
    }

  } catch(err) {
    console.error('Build error:', err);
    process.exit(1);
  }
}

main();
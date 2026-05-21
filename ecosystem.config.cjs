module.exports = {
  apps: [
    {
      name: 'llm-oriagent',
      script: './backend/start.sh',
      cwd: '/home/step/llm_oriagent',
      interpreter: 'bash',
      env: {
        PORT: '8089',
        HOST: '127.0.0.1',
        OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
        WEBUI_SECRET_KEY: 'llm_oriagent_secret_secure_key_2026',
        FRONTEND_BUILD_DIR: '/home/step/llm_oriagent/build',
        VIRTUAL_ENV: '/home/step/llm_oriagent/.venv',
        PATH: '/home/step/llm_oriagent/.venv/bin:/home/step/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
      },
      restart_delay: 3000,
      max_restarts: 10,
      error_file: '/home/step/.pm2/logs/llm-oriagent-error.log',
      out_file: '/home/step/.pm2/logs/llm-oriagent-out.log'
    }
  ]
};

server {
    server_name llm.oriagent.com;

    client_max_body_size 100M;
    proxy_connect_timeout 1800;
    proxy_send_timeout 1800;
    proxy_read_timeout 1800;
    send_timeout 1800;

    location /ws/ {
        proxy_pass http://127.0.0.1:8089/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:8089/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location / {
        proxy_pass http://127.0.0.1:8089/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # --- Streaming / SSE fix: disable Nginx buffering ---
        proxy_buffering off;
        proxy_cache off;
        proxy_request_buffering off;
        chunked_transfer_encoding on;
        proxy_set_header X-Accel-Buffering no;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/llm.oriagent.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/llm.oriagent.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot


}
server {
    if ($host = llm.oriagent.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name llm.oriagent.com;
    return 404; # managed by Certbot


}

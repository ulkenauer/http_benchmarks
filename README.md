```python
hypercorn http_app:app --config hypercorn.toml --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
```

```
history | grep hypercorn                                                                                                
  960  uv add hypercorn
  961  uv add hypercorn[h3]
  962  uv add 'hypercorn[h3]'
  963  uv add 'hypercorn[h3]'
  964  hypercorn --help
  965  hypercorn http_app:app --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  967  hypercorn http_app:app --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  968  hypercorn --help
  969  hypercorn http_app:app --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  970  hypercorn --help
  971  hypercorn http_app:app --config hypercorn.toml --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  972  hypercorn http_app:app --config hypercorn.toml --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  973  hypercorn http_app:app --config hypercorn.toml --quic-bind localhost:4433 --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
  974  hypercorn http_app:app --config hypercorn.toml --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem
```


```
uvicorn http_app:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem --http h11
```
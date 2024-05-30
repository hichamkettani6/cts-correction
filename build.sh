#!/bin/bash
#!/bin/bash
if [ ! -e "$PWD/.env" ]; then
  echo "make .env file from .env.template"
  exit 0
fi
source .env
docker build --rm -f Dockerfile . --build-arg TZ=$TZ --no-cache --network host -t cts_correction:latest
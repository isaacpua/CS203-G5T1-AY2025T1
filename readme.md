# Installation

- Spring Boot Java version = JDK-17 (as per Intro slides)
- Node 22+ (or at least that's what has been tested to be working so far)

# Development

## React Frontend

```
cd tariff-frontend
npm install
npm run dev
```

## Java Springboot Backend

```
cd tariff-backend
./mvnw clean spring-boot:run
```

## Python Logic Backend
For macOS/Linux:
``` 
cd python-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
For Windows:
```
cd python-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

```
cd src
fastapi dev app.py --port 8001
```


## Python MCP Server Backend

For macOS/Linux:
``` 
cd MCP-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fastapi run
```
For Windows:
```
cd MCP-server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
fastapi run
```


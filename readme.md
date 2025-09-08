# Installation

- Spring Boot Java version = JDK-17 (as per Intro slides)
- Node 22+ (or at least that's what has been tested to be working so far)

## Frontend

```
cd tariff-frontend
npm i recharts
npm install
```

# Development

## Frontend

```
cd tariff-frontend
npm run dev
```

## Backend

```
cd tariff-backend
./mvnw clean spring-boot:run
```

``` Postgres Database Connection Test
./mvnw test  
```

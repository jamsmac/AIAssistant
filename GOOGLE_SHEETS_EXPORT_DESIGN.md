# Google Sheets Export - Design Document

## 📊 Export Structure

### Sheet 1: Summary
```
| Field                | Value                    |
|---------------------|--------------------------|
| API Name            | Swagger Petstore         |
| API Version         | 1.0.0                    |
| Spec Version        | 2.0                      |
| Total Endpoints     | 20                       |
| Total Schemas       | 6                        |
| Analyzed Date       | 2025-11-08 20:00:00      |
| Document ID         | cb752f97-...             |
```

### Sheet 2: Endpoints
```
| Method | Path              | Summary                  | Description | Parameters | Request Body | Responses |
|--------|-------------------|--------------------------|-------------|------------|--------------|-----------|
| GET    | /pet/{petId}      | Find pet by ID           | Returns...  | petId (path) | -          | 200, 400, 404 |
| POST   | /pet              | Add a new pet to store   | -           | body (Pet)   | Pet object | 405       |
...
```

### Sheet 3: Schemas
```
| Schema Name | Type   | Properties Count | Required Fields | Generated SQL         |
|-------------|--------|------------------|----------------|-----------------------|
| Pet         | object | 6                | name, photoUrls| CREATE TABLE pet (...)|
| User        | object | 8                | -              | CREATE TABLE user (...)|
...
```

### Sheet 4: Schema Details
```
| Schema Name | Property Name | Type    | Required | Description        |
|-------------|---------------|---------|----------|--------------------|
| Pet         | id            | integer | No       | Pet ID             |
| Pet         | name          | string  | Yes      | Pet name           |
| Pet         | status        | string  | No       | Pet status         |
...
```

## 🔐 Authentication

### Option 1: Service Account (Recommended)
- Create service account in Google Cloud Console
- Download JSON key file
- Set environment variable: `GOOGLE_SHEETS_CREDENTIALS_PATH`
- Share sheet with service account email

### Option 2: OAuth (Alternative)
- User authorizes access
- Token stored per user
- Better for multi-user scenarios

## 🎨 Formatting

- **Headers**: Bold, background color
- **HTTP Methods**: Color-coded (GET=green, POST=blue, DELETE=red)
- **Auto-resize columns**
- **Freeze header row**
- **Links to documentation**

## 📝 Implementation Plan

1. Install dependencies: `gspread`, `google-auth`
2. Create `sheets_exporter.py` service
3. Add export endpoint to API
4. Add "Export to Sheets" button in UI
5. Test with Petstore data

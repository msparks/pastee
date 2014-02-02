# Pastee API

## Get a paste

    GET /pastes/{id}

### Response

    {
      "content": "Paste content.",
    }

## Create a new paste

    POST /pastes

### Input

    {
      "content": "Paste content.",
      "expiry": "2014-02-01T18:17:35.999118-08:00"
    }

### Parameters

| Name         | Type      | Description  |
| ---          | ----      | -----------  |
| `content`    | `string`  | **Required**. Paste content in UTF-8. |
| `mac`        | `string`  | Hex digest of a Message Authentication Code (MAC) for `content`. |
| `expiry`     | `string`  | Expiration date in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ` |

### Response

    Status: 201 Created
    Location: https://api.pastee.com/pastes/{id}

    {
      "id": "3x35aba",
    }

### Limits

The server MAY enforce a maximum lifetime or `content` size.

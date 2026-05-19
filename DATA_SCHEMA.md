# SWork Data Schema

## leads.csv

```csv
id,source_url,source_name,company_name,branch,website_url,email,contact_form_url,phone,address,industry,hypothesis,status,last_contacted_at,next_action,notes
```

## ステータス

- `new`
- `researched`
- `drafted`
- `sent`
- `form_ready`
- `replied`
- `meeting`
- `not_interested`
- `invalid`

## replies.csv

```csv
id,lead_id,received_at,from_address,subject,body_summary,status,next_action,notes
```

## messages.csv

```csv
id,lead_id,channel,created_at,sent_at,subject,body,status,result,notes
```


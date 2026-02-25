# Moccha

Flask API Server untuk eksekusi kode Python dan manajemen file.

## Instalasi

```bash
pip install -r requirements.txt
```

## Konfigurasi

```bash
export MOCCHA_API_KEY=your_secret_key
export MOCCHA_WORKSPACE=/path/to/workspace
```

## Penggunaan

```bash
python -m moccha.app
```

## API Endpoints

- `GET /` - Informasi service
- `GET /ping` - Test koneksi
- `GET /status` - Status sistem
- `POST /execute` - Eksekusi kode
- `POST /shell` - Eksekusi shell
- `POST /install` - Install package
- `GET /files` - List file
- `POST /upload` - Upload file
- `GET /download/<path>` - Download file
- `POST /async-execute` - Eksekusi async
- `GET /task/<tid>` - Status task
- `GET /variables` - List variables
- `DELETE /variables/<name>` - Delete variable
- `GET /history` - Execution history
- `GET /services` - List service eksternal (deluge, jdownloader, mega)
- `POST /services/<name>/action` - Aksi ke service eksternal

### Contoh panggilan service eksternal

#### Deluge

```bash
curl -X POST "$URL/services/deluge/action" \
  -H "X-API-Key: $MOCCHA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"add_magnet","payload":{"magnet":"magnet:?xt=urn:btih:..."}}'
```

Env yang dibutuhkan:

- `DELUGE_URL` (contoh: `http://127.0.0.1:8112`)
- `DELUGE_PASSWORD`

#### JDownloader

```bash
curl -X POST "$URL/services/jdownloader/action" \
  -H "X-API-Key: $MOCCHA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"add_links","payload":{"links":["https://example.com/file.zip"]}}'
```

Env yang dibutuhkan:

- `MYJD_EMAIL`
- `MYJD_PASSWORD`
- `MYJD_DEVICE` (opsional)

#### Mega

```bash
curl -X POST "$URL/services/mega/action" \
  -H "X-API-Key: $MOCCHA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"download_url","payload":{"url":"https://mega.nz/xxx","dest":"/content"}}'
```

Env yang dibutuhkan:

- `MEGA_EMAIL`
- `MEGA_PASSWORD`
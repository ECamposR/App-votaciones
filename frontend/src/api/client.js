function readCookie(name) {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')
    .slice(1)
    .join('=') ?? null
}

function isFormData(value) {
  return typeof FormData !== 'undefined' && value instanceof FormData
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  if (response.status === 204) {
    return null
  }
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

async function parseError(response) {
  const payload = await parseResponse(response)
  const detail = typeof payload === 'string' ? payload : payload?.detail
  const error = new Error(detail || `Request failed with status ${response.status}`)
  error.status = response.status
  error.payload = payload
  return error
}

let refreshPromise = null

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...(readCookie('csrftoken') ? { 'x-csrftoken': readCookie('csrftoken') } : {}),
      },
    }).finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export async function request(path, options = {}) {
  const {
    method = 'GET',
    json,
    headers = {},
    skipRefresh = false,
    ...rest
  } = options

  const finalHeaders = new Headers(headers)
  const csrfToken = readCookie('csrftoken')
  const unsafeMethod = !['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())

  if (json !== undefined && !isFormData(json)) {
    finalHeaders.set('Content-Type', 'application/json')
  }
  if (unsafeMethod && csrfToken && !finalHeaders.has('x-csrftoken')) {
    finalHeaders.set('x-csrftoken', csrfToken)
  }

  const response = await fetch(path, {
    ...rest,
    method,
    headers: finalHeaders,
    credentials: 'include',
    body:
      json === undefined
        ? rest.body
        : isFormData(json)
          ? json
          : JSON.stringify(json),
  })

  if (response.status === 401 && !skipRefresh && path !== '/auth/refresh') {
    const refreshed = await refreshAccessToken()
    if (refreshed.ok) {
      return request(path, { ...options, skipRefresh: true })
    }
  }

  if (!response.ok) {
    throw await parseError(response)
  }

  return parseResponse(response)
}

export async function downloadFile(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
  })

  if (!response.ok) {
    throw await parseError(response)
  }

  return response.blob()
}

export { readCookie }

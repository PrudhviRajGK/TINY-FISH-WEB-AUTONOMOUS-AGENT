async function readResponse(response) {
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
        return response.json();
    }

    return response.text();
}

export async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await readResponse(response);

    if (!response.ok) {
        const errorMessage =
            data?.detail ||
            data?.error ||
            data?.message ||
            'Request failed.';

        throw new Error(errorMessage);
    }

    return data;
}

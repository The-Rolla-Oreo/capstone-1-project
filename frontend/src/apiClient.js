// src/apiClient.js
const API_BASE_URL = 'https://capstone-1-project-1jhl.onrender.com';

/**
 * A wrapper for the fetch API to prepend the API base URL and handle credentials.
 * @param {string} endpoint The API endpoint to call (e.g., '/users').
 * @param {RequestInit} options The options for the fetch request.
 * @returns {Promise<Response>} The fetch promise.
 */
const apiClient = (endpoint, options = {}) => {
  // Ensure the endpoint starts with a slash
  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${formattedEndpoint}`;

  const headers = {
    ...options.headers,
  };

  // Do not set Content-Type for FormData, browser does it automatically
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const newOptions = {
    ...options,
    headers,
    // This is crucial for sending HttpOnly cookies on cross-origin requests
    credentials: 'include',
  };

  return fetch(url, newOptions);
};

export default apiClient;

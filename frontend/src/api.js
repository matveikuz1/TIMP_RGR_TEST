import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    withCredentials: true,
});

// Перехватчик ответов для обработки ошибок
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error?.response?.status;
        const requestUrl = error?.config?.url || '';
        const isShareRequest = requestUrl.startsWith('/share/');
        const isRefreshRequest = requestUrl.startsWith('/auth/refresh');
        const isSharePage = window.location.pathname.startsWith('/share/');
        
        // Не обрабатываем 401 для запроса на обновление токена и для публичных страниц
        if (status === 401 && !isRefreshRequest && window.location.pathname !== '/login' && !isShareRequest && !isSharePage) {
//            window.location.href = '/login';
        }
        
        if (status === 403) {
            const message = error?.response?.data?.message || 'Недостаточно прав';
            window.alert(message);
        }
        
        return Promise.reject(error);
    }
);

export default api;

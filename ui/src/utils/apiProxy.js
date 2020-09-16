
class APIProxy{
    static BASE_URL='http://localhost:8888';

    static getUrl(url, success, error){
        fetch(`${APIProxy.BASE_URL}/${url}`).then(resp => resp.json()).then(success).catch(error);
    }

    static getRawUrl(url, success, error){
        fetch(`${APIProxy.BASE_URL}/${url}`).then(resp => resp.blob()).then(success).catch(error);
    }

    static putUrl(url, data, success, error){
        fetch(`${APIProxy.BASE_URL}/${url}`, 
                { 
                    method:'PUT',
                    body:JSON.stringify(data),
                    headers: { 'Content-Type': 'application/json' }
                }
            ).then(resp => resp.json()).then(success).catch(error);
    }
}

export default APIProxy;

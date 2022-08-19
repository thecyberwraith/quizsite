export function getURLFromLocation(relative_from_root_url) {
    return getURLFromLocationWithProtocol(
        window.location.protocol,
        relative_from_root_url
    );
}

export function getWebsocketURLFromLocation(relative_from_root_url) {
    let protocol = 'ws:'

    if (window.location.protocol == 'https:')
        protocol = 'wss:'
    
    return getURLFromLocationWithProtocol(protocol, relative_from_root_url);
}

function getURLFromLocationWithProtocol(protocol, relative_url) {
    return protocol + '//'
        + window.location.host
        + relative_url
}
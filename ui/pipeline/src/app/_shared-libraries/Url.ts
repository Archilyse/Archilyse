/**
 * Helper function to parse the String parameters of a URL
 * ?param1=val1&param2=val2....
 * @param str
 */
export function parseParams(str) {
  const data = {};
  if (str) {
    const pieces = str.split('&');
    let i;
    let parts;

    // process each query pair
    for (i = 0; i < pieces.length; i += 1) {
      parts = pieces[i].split('=');
      if (parts.length < 2) {
        parts.push('');
      }
      data[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1]);
    }
  }
  return data;
}

/**
 * Formats errors properly
 * @param e
 */
export function parseErrorObj(e) {
  if (e.error) {
    if (e.error.msg) {
      return e.error.msg;
    }
    if (e.error.message) {
      return e.error.message;
    }
    if (typeof e.error === 'string') {
      return e.error;
    }
  }
  if (e.message) {
    return e.message;
  }
  return e;
}

let baseLink = null;

/**
 * function to download the final file
 */
export function saveData(fileName, data) {
  // If the link is not created we create it
  if (!baseLink) {
    baseLink = document.createElement('a');
    document.body.appendChild(baseLink);
  }

  const blob = new Blob([data], { type: 'octet/stream' });
  const url = window.URL.createObjectURL(blob);
  baseLink.href = url;
  baseLink.download = fileName;
  baseLink.click();
  window.URL.revokeObjectURL(url);
}

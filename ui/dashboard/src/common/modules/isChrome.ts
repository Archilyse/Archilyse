const currentWindow: any = window;
const isChrome = () => !!currentWindow.chrome && (!!currentWindow.chrome.webstore || !!currentWindow.chrome.runtime);

export default isChrome;

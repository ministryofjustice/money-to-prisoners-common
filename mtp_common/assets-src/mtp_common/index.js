// mtp-common components required by all apps
import {Analytics} from './components/analytics';
import {ElementFocus} from './components/element-focus';

export function initDefaults () {
  Analytics.init();
  ElementFocus.init();
}

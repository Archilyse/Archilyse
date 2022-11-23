import { v4 as uuidv4 } from 'uuid';

export class IDBroker {
  static acquireID() {
    return uuidv4();
  }
}

export default IDBroker;

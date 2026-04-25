export interface Pdf417BarcodeArray {
  bcode: number[][];
  num_cols: number;
  num_rows: number;
}

export interface Pdf417Global {
  init(text: string): void;
  getBarcodeArray(): Pdf417BarcodeArray;
}

declare global {
  interface Window {
    PDF417?: Pdf417Global;
    libbcmath?: unknown;
  }
}

export {};

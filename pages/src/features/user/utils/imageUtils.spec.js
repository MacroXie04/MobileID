import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import {
  validateImageFile,
  fileToBase64,
  createImageObjectURL,
  getImageDimensions,
  validateImageDimensions,
} from '@user/utils/imageUtils.js';

describe('imageUtils', () => {
  let originalURL;
  let originalImage;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock URL
    originalURL = global.URL;
    global.URL = {
      createObjectURL: vi.fn(() => 'blob:mock-url-123'),
      revokeObjectURL: vi.fn(),
    };
  });

  afterEach(() => {
    global.URL = originalURL;
  });

  describe('validateImageFile', () => {
    it('should return success for valid JPEG file', () => {
      const file = {
        type: 'image/jpeg',
        size: 1024 * 1024, // 1MB
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should return success for valid PNG file', () => {
      const file = {
        type: 'image/png',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should return success for valid GIF file', () => {
      const file = {
        type: 'image/gif',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should return success for valid WebP file', () => {
      const file = {
        type: 'image/webp',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should return success for valid JPG file (alternate MIME)', () => {
      const file = {
        type: 'image/jpg',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should reject PDF files', () => {
      const file = {
        type: 'application/pdf',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(false);
      expect(result.error).toContain('JPG, PNG, GIF, or WebP');
    });

    it('should reject SVG files', () => {
      const file = {
        type: 'image/svg+xml',
        size: 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(false);
    });

    it('should reject BMP files', () => {
      const file = {
        type: 'image/bmp',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(false);
    });

    it('should reject files exceeding maxSizeMB (default 5MB)', () => {
      const file = {
        type: 'image/jpeg',
        size: 6 * 1024 * 1024, // 6MB
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(false);
      expect(result.error).toContain('5MB');
    });

    it('should accept files at exactly maxSizeMB', () => {
      const file = {
        type: 'image/jpeg',
        size: 5 * 1024 * 1024, // exactly 5MB
      };

      const result = validateImageFile(file);

      expect(result.success).toBe(true);
    });

    it('should return error for null file', () => {
      const result = validateImageFile(null);

      expect(result.success).toBe(false);
      expect(result.error).toBe('No file selected');
    });

    it('should return error for undefined file', () => {
      const result = validateImageFile(undefined);

      expect(result.success).toBe(false);
      expect(result.error).toBe('No file selected');
    });

    it('should use custom allowedTypes regex', () => {
      const file = {
        type: 'image/tiff',
        size: 1024 * 1024,
      };

      const result = validateImageFile(file, {
        allowedTypes: /^image\/tiff$/i,
      });

      expect(result.success).toBe(true);
    });

    it('should use custom maxSizeMB', () => {
      const file = {
        type: 'image/jpeg',
        size: 2 * 1024 * 1024, // 2MB
      };

      const result = validateImageFile(file, { maxSizeMB: 1 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('1MB');
    });

    it('should accept larger files with increased maxSizeMB', () => {
      const file = {
        type: 'image/jpeg',
        size: 8 * 1024 * 1024, // 8MB
      };

      const result = validateImageFile(file, { maxSizeMB: 10 });

      expect(result.success).toBe(true);
    });
  });

  describe('fileToBase64', () => {
    it('should convert file to base64 with prefix removed (default)', async () => {
      const mockFile = new Blob(['test'], { type: 'image/jpeg' });
      const mockResult = 'data:image/jpeg;base64,dGVzdA==';

      // Create mock FileReader class
      class MockFileReader {
        constructor() {
          this.result = mockResult;
          this.onloadend = null;
          this.onerror = null;
        }
        readAsDataURL() {
          // Simulate async behavior
          setTimeout(() => this.onloadend?.(), 0);
        }
      }
      global.FileReader = MockFileReader;

      const result = await fileToBase64(mockFile);

      expect(result).toBe('dGVzdA=='); // Prefix removed
    });

    it('should keep prefix when removePrefix is false', async () => {
      const mockFile = new Blob(['test'], { type: 'image/jpeg' });
      const mockResult = 'data:image/jpeg;base64,dGVzdA==';

      class MockFileReader {
        constructor() {
          this.result = mockResult;
          this.onloadend = null;
          this.onerror = null;
        }
        readAsDataURL() {
          setTimeout(() => this.onloadend?.(), 0);
        }
      }
      global.FileReader = MockFileReader;

      const result = await fileToBase64(mockFile, false);

      expect(result).toBe('data:image/jpeg;base64,dGVzdA=='); // Prefix kept
    });

    it('should reject on FileReader error', async () => {
      const mockFile = new Blob(['test'], { type: 'image/jpeg' });
      const mockError = new Error('Read failed');

      class MockFileReader {
        constructor() {
          this.result = null;
          this.onloadend = null;
          this.onerror = null;
        }
        readAsDataURL() {
          setTimeout(() => this.onerror?.(mockError), 0);
        }
      }
      global.FileReader = MockFileReader;

      await expect(fileToBase64(mockFile)).rejects.toEqual(mockError);
    });
  });

  describe('createImageObjectURL', () => {
    it('should create object URL for file', () => {
      const file = new Blob(['test'], { type: 'image/jpeg' });

      const result = createImageObjectURL(file);

      expect(global.URL.createObjectURL).toHaveBeenCalledWith(file);
      expect(result).toBe('blob:mock-url-123');
    });

    it('should revoke previous URL if provided', () => {
      const file = new Blob(['test'], { type: 'image/jpeg' });
      const previousUrl = 'blob:old-url-456';

      createImageObjectURL(file, previousUrl);

      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith(previousUrl);
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(file);
    });

    it('should not revoke if previousUrl is null', () => {
      const file = new Blob(['test'], { type: 'image/jpeg' });

      createImageObjectURL(file, null);

      expect(global.URL.revokeObjectURL).not.toHaveBeenCalled();
    });

    it('should not revoke if previousUrl is undefined', () => {
      const file = new Blob(['test'], { type: 'image/jpeg' });

      createImageObjectURL(file);

      expect(global.URL.revokeObjectURL).not.toHaveBeenCalled();
    });
  });

  describe('getImageDimensions', () => {
    beforeEach(() => {
      originalImage = global.Image;
    });

    afterEach(() => {
      global.Image = originalImage;
    });

    it('should load image and return dimensions', async () => {
      class MockImage {
        constructor() {
          this.onload = null;
          this.onerror = null;
          this.width = 0;
          this.height = 0;
        }
        set src(value) {
          // Simulate async image load
          setTimeout(() => {
            this.width = 800;
            this.height = 600;
            this.onload?.();
          }, 0);
        }
      }
      global.Image = MockImage;

      const result = await getImageDimensions('http://example.com/image.jpg');

      expect(result).toEqual({ width: 800, height: 600 });
    });

    it('should reject on image load error', async () => {
      class MockImage {
        constructor() {
          this.onload = null;
          this.onerror = null;
        }
        set src(value) {
          setTimeout(() => {
            this.onerror?.(new Error('Load failed'));
          }, 0);
        }
      }
      global.Image = MockImage;

      await expect(getImageDimensions('http://example.com/bad-image.jpg')).rejects.toThrow();
    });
  });

  describe('validateImageDimensions', () => {
    beforeEach(() => {
      originalImage = global.Image;

      // Default mock for 800x600 image
      class MockImage {
        constructor() {
          this.onload = null;
          this.onerror = null;
          this.width = 0;
          this.height = 0;
        }
        set src(value) {
          setTimeout(() => {
            this.width = 800;
            this.height = 600;
            this.onload?.();
          }, 0);
        }
      }
      global.Image = MockImage;
    });

    afterEach(() => {
      global.Image = originalImage;
    });

    it('should return success when no limits specified', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg');

      expect(result.success).toBe(true);
      expect(result.dimensions).toEqual({ width: 800, height: 600 });
    });

    it('should validate minWidth', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        minWidth: 1000,
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('at least 1000px');
    });

    it('should pass minWidth when image is large enough', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        minWidth: 500,
      });

      expect(result.success).toBe(true);
    });

    it('should validate minHeight', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        minHeight: 700,
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('at least 700px');
    });

    it('should pass minHeight when image is tall enough', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        minHeight: 400,
      });

      expect(result.success).toBe(true);
    });

    it('should validate maxWidth', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        maxWidth: 500,
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('at most 500px');
    });

    it('should pass maxWidth when image is small enough', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        maxWidth: 1000,
      });

      expect(result.success).toBe(true);
    });

    it('should validate maxHeight', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        maxHeight: 400,
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('at most 400px');
    });

    it('should pass maxHeight when image is short enough', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        maxHeight: 800,
      });

      expect(result.success).toBe(true);
    });

    it('should validate multiple constraints', async () => {
      const result = await validateImageDimensions('http://example.com/image.jpg', {
        minWidth: 100,
        minHeight: 100,
        maxWidth: 1000,
        maxHeight: 1000,
      });

      expect(result.success).toBe(true);
      expect(result.dimensions).toEqual({ width: 800, height: 600 });
    });

    it('should return error when image fails to load', async () => {
      class FailingImage {
        constructor() {
          this.onload = null;
          this.onerror = null;
        }
        set src(value) {
          setTimeout(() => {
            this.onerror?.(new Error('Failed'));
          }, 0);
        }
      }
      global.Image = FailingImage;

      const result = await validateImageDimensions('http://example.com/bad.jpg');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to load image');
    });
  });
});

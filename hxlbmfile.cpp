#include "hxlbmpfile.h"

HXLBMPFILE::HXLBMPFILE() {
	pImageData=NULL;
	for (int i = 0; i < 256; i++) {
		rgbPalette[i].rgbBlue =
			rgbPalette[i].rgbGreen =
			rgbPalette[i].rgbRed = i;
		rgbPalette[i].rgbReserved = 0;
	}
	iYRGBnum = 0;
	iImagew = iImageh = 0;
}

HXLBMPFILE::~HXLBMPFILE() {
	if (pImageData)
		delete[] pImageData;
}

BOOL HXLBMPFILE::IsBMPFile(FILE* f) {
	fseek(f, 0, SEEK_END);
	int flen = ftell(f);

	BITMAPFILEHEADER fh;
	fseek(f, 0, SEEK_SET);
	fread(&fh, sizeof(BITMAPFILEHEADER), 1, f);
	if (fh.bfType != 0x4d42) {
		printf("  [DBG] bfType mismatch: 0x%X\n", fh.bfType); fflush(stdout);
		fclose(f);
		return false;
	}
	if (fh.bfSize != flen) {
		printf("  [DBG] bfSize=%d but flen=%d\n", fh.bfSize, flen); fflush(stdout);
		fclose(f);
		return false;
	}
	return true;
}

BOOL HXLBMPFILE::IspImageDataOk() {
	int size = iImagew * iImageh * iYRGBnum;
	if (pImageData) {
		delete[] pImageData;
		pImageData = NULL;
	}
	pImageData = new BYTE[size];
	if (pImageData)
		memset(pImageData, 0, size);
	return pImageData != NULL;
}

int HXLBMPFILE::GetBytes1Line() {
	return (iImagew * iYRGBnum + 3) / 4 * 4;
}

BOOL HXLBMPFILE::GetPara(FILE* f) {
	BITMAPINFOHEADER ih;
	fread(&ih, sizeof(BITMAPINFOHEADER), 1, f);
	if (ih.biBitCount != 8) {
		if (ih.biBitCount != 24) {
			fclose(f);
			return FALSE;
		}
	}
	iYRGBnum = ih.biBitCount / 8;
	iImagew = ih.biWidth;
	iImageh = ih.biHeight;
	fseek(f, 14 + ih.biSize, SEEK_SET);
	if (iYRGBnum == 1)
		fread(rgbPalette, sizeof(RGBQUAD), 256, f);
	return TRUE;
}

BYTE* HXLBMPFILE::pDataAt(int h, int Y0R0G1B2) {
	int iRGB = Y0R0G1B2 * iImagew * iImageh;
	if (iYRGBnum <= Y0R0G1B2) iRGB = 0;
	return pImageData + h * iImagew + iRGB;
}

BOOL HXLBMPFILE::Get8BMPData(FILE* f) {
	int w4b = GetBytes1Line();
	BYTE* ptr = NULL;
	ptr = new BYTE[w4b];
	if (!ptr) return FALSE;
	for (int i = iImageh - 1; i >= 0; i--) {
		fread(ptr, w4b, 1, f);
		memmove(pDataAt(i), ptr, iImagew);
	}
	delete[] ptr;
	return TRUE;
}

BOOL HXLBMPFILE::Get24BMPData(FILE* f) {
	int w4b = GetBytes1Line();
	BYTE* ptr = NULL;
	ptr = new BYTE[w4b];
	if (!ptr) return FALSE;
	for (int i = iImageh - 1; i >= 0; i--) {
		fread(ptr, w4b, 1, f);
		for (int j = 0; j < iImagew; j++) {
			*(pDataAt(i, 0) + j) = *(ptr + j * 3 + 2);
			*(pDataAt(i, 1) + j) = *(ptr + j * 3 + 1);
			*(pDataAt(i, 2) + j) = *(ptr + j * 3 + 0);
		}
	}
	delete[] ptr;
	return TRUE;
}

BOOL HXLBMPFILE::LoadBMPFile(char* cFname) {
	printf("  [DBG] LoadBMPFile start\n"); fflush(stdout);
	if (strlen(cFname) < 5) return FALSE;
	FILE* f = NULL;
	f = fopen(cFname, "rb");
	if (f == NULL) { printf("  [DBG] fopen failed\n"); fflush(stdout); return FALSE; }
	printf("  [DBG] fopen OK\n"); fflush(stdout);

	if (!IsBMPFile(f)) { printf("  [DBG] IsBMPFile failed\n"); fflush(stdout); return FALSE; }
	printf("  [DBG] IsBMPFile OK\n"); fflush(stdout);

	if (!GetPara(f)) { printf("  [DBG] GetPara failed\n"); fflush(stdout); fclose(f); return FALSE; }
	printf("  [DBG] GetPara OK: w=%d h=%d bits=%d\n", iImagew, iImageh, iYRGBnum * 8); fflush(stdout);

	if (!IspImageDataOk()) { printf("  [DBG] IspImageDataOk failed\n"); fflush(stdout); fclose(f); return FALSE; }
	printf("  [DBG] IspImageDataOk OK\n"); fflush(stdout);

	BOOL res = FALSE;
	if (iYRGBnum == 1)
		res = Get8BMPData(f);
	else if (iYRGBnum == 3)
		res = Get24BMPData(f);
	printf("  [DBG] GetData res=%d\n", res); fflush(stdout);

	fclose(f);
	return res;
}

void HXLBMPFILE::SaveFileHeader(FILE* f) {
	BITMAPFILEHEADER fh;
	memset(&fh, 0, sizeof(BITMAPFILEHEADER));
	fh.bfType = 0x4d42;
	fh.bfOffBits = 14 + 40 + ((iYRGBnum == 1) ? 256 * sizeof(RGBQUAD) : 0);
	fh.bfSize = fh.bfOffBits + iImageh * GetBytes1Line();
	fwrite(&fh, sizeof(BITMAPFILEHEADER), 1, f);
}

void HXLBMPFILE::SaveInfoHeader(FILE* f) {
	BITMAPINFOHEADER ih;
	memset(&ih, 0, sizeof(BITMAPINFOHEADER));
	ih.biSize = 40; ih.biPlanes = 1;
	ih.biWidth = iImagew; ih.biHeight = iImageh;
	ih.biBitCount = 8 * iYRGBnum;
	ih.biSizeImage = iImageh * GetBytes1Line();
	fwrite(&ih, sizeof(BITMAPINFOHEADER), 1, f);
	if (iYRGBnum == 1)
		fwrite(rgbPalette, sizeof(RGBQUAD), 256, f);
}

BOOL HXLBMPFILE::Save8BMPData(FILE* f) {
	int w4b = GetBytes1Line();
	BYTE* ptr = new BYTE[w4b];
	if (ptr == NULL) return FALSE;
	memset(ptr, 0, w4b);
	for (int i = iImageh - 1; i >= 0; i--) {
		memmove(ptr, pDataAt(i), iImagew);
		fwrite(ptr, w4b, 1, f);
	}
	delete[] ptr;
	return TRUE;
}

BOOL HXLBMPFILE::Save24BMPData(FILE* f) {
	int w4b = GetBytes1Line();
	BYTE* ptr = new BYTE[w4b];
	if (ptr == NULL) return FALSE;
	memset(ptr, 0, w4b);
	for (int i = iImageh - 1; i >= 0; i--) {
		for (int j = 0; j < iImagew; j++) {
			*(ptr + j * 3 + 2) = *(pDataAt(i, 0) + j);
			*(ptr + j * 3 + 1) = *(pDataAt(i, 1) + j);
			*(ptr + j * 3 + 0) = *(pDataAt(i, 2) + j);
		}
		fwrite(ptr, w4b, 1, f);
	}
	delete[] ptr;
	return TRUE;
}

BOOL HXLBMPFILE::SaveBMPFile(char* cFname) {
	if (!pImageData) return FALSE;
	if (strlen(cFname) < 5) return FALSE;

	FILE* f = NULL;
	f = fopen(cFname, "w+b");
	if (f == NULL) return FALSE;
	SaveFileHeader(f);
	SaveInfoHeader(f);

	BOOL res = FALSE;
	if (iYRGBnum == 1) res = Save8BMPData(f);
	else if (iYRGBnum == 3) res = Save24BMPData(f);
	fclose(f);
	return res;
}
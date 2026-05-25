#include "hxlbmpfile.h"
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// 函数1：统计图像直方图函数
// 输入：图像类指针；输出：直方图数组H[256]（归一化概率）
void CalcHistogram(HXLBMPFILE* bmp, float H[256]) {
    memset(H, 0, 256 * sizeof(float));
    int total = bmp->iImageh * bmp->iImagew;
    for (int i = 0; i < bmp->iImageh; i++)
        for (int j = 0; j < bmp->iImagew; j++)
            H[bmp->pDataAt(i)[j]] += 1.0f;
    // 归一化为概率
    for (int k = 0; k < 256; k++)
        H[k] /= (float)total;
}

// 函数2：直方图均衡化变换函数
// 输入：直方图H[256]（归一化概率）；输出：变换函数T[256]（BYTE映射表）
void CalcEqualizationTransform(float H[256], BYTE T[256]) {
    float cdf[256];
    cdf[0] = H[0];
    for (int i = 1; i < 256; i++)
        cdf[i] = cdf[i - 1] + H[i];
    for (int i = 0; i < 256; i++)
        T[i] = (BYTE)(cdf[i] * 255.0f + 0.5f);
}

// 函数3：目标直方图生成函数（正弦函数 y=sin(x), x∈[0,π]）
// 输入：无；输出：目标直方图Hdd[256]（归一化概率）
void GenerateTargetHistogram(float Hdd[256]) {
    float sum = 0.0f;
    for (int k = 0; k < 256; k++) {
        // 将 k 映射到 [0, π]
        float x = (float)k / 255.0f * (float)M_PI;
        Hdd[k] = sinf(x);
        sum += Hdd[k];
    }
    // 归一化使总和为1
    for (int k = 0; k < 256; k++)
        Hdd[k] /= sum;
}

// 函数4：规定化变换函数
// 输入：原图直方图Hs、目标直方图Hdd；输出：规定化变换函数Td[256]
// 方法：SML（单映射法）
//   1) 计算原图均衡化CDF: Ts[k] = round(sum(Hs[0..k]) * 255)
//   2) 计算目标均衡化CDF: Tdd[k] = round(sum(Hdd[0..k]) * 255)
//   3) 对每个灰度k，找到使 |Ts[k] - Tdd[j]| 最小的j，令Td[k] = j
void CalcSpecificationTransform(float Hs[256], float Hdd[256], BYTE Td[256]) {
    // 原图均衡化映射
    BYTE Ts[256];
    CalcEqualizationTransform(Hs, Ts);

    // 目标直方图均衡化映射
    BYTE Tdd[256];
    CalcEqualizationTransform(Hdd, Tdd);

    // 对每个灰度级 k，在目标CDF中查找最近匹配
    for (int k = 0; k < 256; k++) {
        int minDiff = 999;
        int bestJ = 0;
        for (int j = 0; j < 256; j++) {
            int diff = abs((int)Ts[k] - (int)Tdd[j]);
            if (diff < minDiff) {
                minDiff = diff;
                bestJ = j;
            }
        }
        Td[k] = (BYTE)bestJ;
    }
}

// 函数5：数组数据文本输出函数
// 输入：数组（float或BYTE）、长度、文件名；输出：txt文件
void SaveArrayToTxt_Float(float arr[256], const char* filename) {
    FILE* fp = fopen(filename, "w");
    if (!fp) { printf("  -> Cannot create %s!\n", filename); return; }
    for (int i = 0; i < 256; i++)
        fprintf(fp, "%d\t%f\n", i, arr[i]);
    fclose(fp);
    printf("  -> %s saved.\n", filename); fflush(stdout);
}

void SaveArrayToTxt_Byte(BYTE arr[256], const char* filename) {
    FILE* fp = fopen(filename, "w");
    if (!fp) { printf("  -> Cannot create %s!\n", filename); return; }
    for (int i = 0; i < 256; i++)
        fprintf(fp, "%d\t%d\n", i, (int)arr[i]);
    fclose(fp);
    printf("  -> %s saved.\n", filename); fflush(stdout);
}

// 函数6：图像变换函数
// 输入：原图像类指针 + 变换函数T[256]；输出：目标图像（新HXLBMPFILE）
void ApplyTransform(HXLBMPFILE* src, BYTE T[256], HXLBMPFILE* dst) {
    dst->iImagew = src->iImagew;
    dst->iImageh = src->iImageh;
    dst->iYRGBnum = 1;
    if (!dst->IspImageDataOk()) return;
    // 复制调色板（灰度）
    for (int k = 0; k < 256; k++) {
        dst->rgbPalette[k].rgbRed = k;
        dst->rgbPalette[k].rgbGreen = k;
        dst->rgbPalette[k].rgbBlue = k;
        dst->rgbPalette[k].rgbReserved = 0;
    }
    for (int i = 0; i < src->iImageh; i++)
        for (int j = 0; j < src->iImagew; j++)
            dst->pDataAt(i)[j] = T[src->pDataAt(i)[j]];
}


int main() {
    HXLBMPFILE bmpIs;  

    printf(" 实验二：直方图规定化处理\n");
    fflush(stdout);

    // 加载原灰度图像 Is
    if (!bmpIs.LoadBMPFile((char*)"b8gray.bmp")) {
        printf("Failed to load b8gray.bmp, trying output_2_gray.bmp...\n");
        fflush(stdout);
    }
    printf("Image loaded: %dx%d, %d-bit\n\n", bmpIs.iImagew, bmpIs.iImageh, bmpIs.iYRGBnum * 8);
    fflush(stdout);

    // ---- 变量声明 ----
    float Hs[256];      // 任务3: 原图直方图
    float Hdd[256];     // 目标直方图（正弦）
    float Hse[256];     // 任务6: 均衡化图像的直方图
    float Hd[256];      // 任务8: 规定化结果图像的直方图
    BYTE Tse[256];      // 任务5: 原图均衡化变换函数
    BYTE Td[256];       // 任务2: 规定化变换函数
    BYTE Tde[256];      // 任务7: 规定化图像的均衡化变换函数

    // 任务3: 计算图像Is的直方图Hs
    printf("[任务3] 计算原图直方图 Hs ...\n"); fflush(stdout);
    CalcHistogram(&bmpIs, Hs);
    SaveArrayToTxt_Float(Hs, "Hs.txt");

    // 任务5: 计算图像Is的均衡化变换函数Tse
    printf("[任务5] 计算均衡化变换函数 Tse ...\n"); fflush(stdout);
    CalcEqualizationTransform(Hs, Tse);
    SaveArrayToTxt_Byte(Tse, "Tse.txt");

    // 任务4: 生成图像Is的均衡化图像Ise
    printf("[任务4] 生成均衡化图像 Ise ...\n"); fflush(stdout);
    HXLBMPFILE bmpIse;
    ApplyTransform(&bmpIs, Tse, &bmpIse);
    bmpIse.SaveBMPFile((char*)"Ise.bmp");
    printf("  -> Ise.bmp saved.\n"); fflush(stdout);

    // 任务6: 计算均衡化图像Ise的直方图Hse
    printf("[任务6] 计算均衡化图像直方图 Hse ...\n"); fflush(stdout);
    CalcHistogram(&bmpIse, Hse);
    SaveArrayToTxt_Float(Hse, "Hse.txt");

    // 生成目标直方图Hdd（正弦函数）
    printf("[准备] 生成目标直方图 Hdd (y=sin(x)) ...\n"); fflush(stdout);
    GenerateTargetHistogram(Hdd);
    SaveArrayToTxt_Float(Hdd, "Hdd.txt");

    // 任务2: 计算直方图规定化变换函数Td
    printf("[任务2] 计算规定化变换函数 Td ...\n"); fflush(stdout);
    CalcSpecificationTransform(Hs, Hdd, Td);
    SaveArrayToTxt_Byte(Td, "Td.txt");

    // 任务1: 生成目标图像Id（直方图规定化结果）
    printf("[任务1] 生成规定化目标图像 Id ...\n"); fflush(stdout);
    HXLBMPFILE bmpId;
    ApplyTransform(&bmpIs, Td, &bmpId);
    bmpId.SaveBMPFile((char*)"d.bmp");
    printf("  -> d.bmp saved.\n"); fflush(stdout);

    // 任务8: 计算规定化图像Id的直方图Hd
    printf("[任务8] 计算规定化图像直方图 Hd ...\n"); fflush(stdout);
    CalcHistogram(&bmpId, Hd);
    SaveArrayToTxt_Float(Hd, "Hd.txt");

    // 任务7: 计算规定化图像Id的均衡化变换函数Tde
    printf("[任务7] 计算规定化图像的均衡化变换函数 Tde ...\n"); fflush(stdout);
    CalcEqualizationTransform(Hd, Tde);
    SaveArrayToTxt_Byte(Tde, "Tde.txt");

    printf("\n==============================\n");
    printf(" 所有任务完成！输出文件：\n");
    printf("  任务1: d.bmp      (规定化目标图像)\n");
    printf("  任务2: Td.txt     (规定化变换函数)\n");
    printf("  任务3: Hs.txt     (原图直方图)\n");
    printf("  任务4: Ise.bmp    (均衡化图像)\n");
    printf("  任务5: Tse.txt    (均衡化变换函数)\n");
    printf("  任务6: Hse.txt    (均衡化图像直方图)\n");
    printf("  任务7: Tde.txt    (规定化图像均衡化变换函数)\n");
    printf("  任务8: Hd.txt     (规定化图像直方图)\n");
    printf("  额外:  Hdd.txt    (目标正弦直方图)\n");
    printf("==============================\n");
    fflush(stdout);

    return 0;
}
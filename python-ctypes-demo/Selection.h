#ifndef SELECTION_H
#define SELECTION_H

#ifdef __cplusplus
extern "C" {
#endif 

#ifdef BUILDING_EXPORT_DLL
#define TYPE_DLL __declspec(dllexport)
#else
#define TYPE_DLL __declspec(dllimport)
#endif

#ifdef __cplusplus
};
#endif

#include <iostream>
#include <cstring>
#include <vector>
using namespace std;

class  TYPE_DLL Selection
{
public:
	Selection();
	~Selection();

	void set_config(float *pts, int _nr, float* _left_bottom, float* _right_top, float* _model_view, float* _proj, int *_viewport, int _stride, int _offset);

	/*** 还可以添加一些helper函数 ***/
	int get_selected_index_size();

	void get_selected_index(int *vec_idx);

private:
	void cal_selected_index();
	void projectXY(float *win_coord, float* modelview, float* proj, int* viewport, float* pos);
	void matrixTransform(float *vOut, float* v, float* m);
	bool drop_in_area(float* x);

private:
	float *pts;
	int nr;
	int offset;
	int stride;

	float *left_bottom;
	float *right_top;
	float *model_view;
	float *proj;
    int *viewport;

	vector<int> vec_selected_pts_index;
};

#ifdef __cplusplus
extern "C" {
#endif

Selection selection;

TYPE_DLL void set_config(float *pts, int _nr, float* _left_bottom, float* _right_top, float* _model_view, float* _proj, int *_viewport, int stride, int offset)
{
	selection.set_config(pts, _nr, _left_bottom, _right_top, _model_view, _proj, _viewport, stride, offset);
}

TYPE_DLL int get_selected_index_size()
{
	return selection.get_selected_index_size();
}

TYPE_DLL void get_selected_index(int *idx)
{
	selection.get_selected_index(idx);
}

#ifdef __cplusplus
};
#endif


#endif // endif

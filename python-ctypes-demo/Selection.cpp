#include "Selection.h"

Selection::Selection()
{
	this->vec_selected_pts_index.clear();
	this->pts = NULL;

	this->left_bottom = new float[2];
	this->right_top = new float[2];

	this->model_view = new float[16];
	this->proj = new float[16];
	this->viewport = new int[4];
}

Selection::~Selection()
{
	if(this->left_bottom){
		delete []this->left_bottom;
		this->left_bottom = NULL;
	}

	if(this->right_top){
		delete [] this->right_top;
		this->right_top = NULL;
	}

	if(this->model_view){
		delete []this->model_view;
		this->model_view = NULL;
	}

	if(this->proj){
		delete []this->proj;
		this->proj = NULL;
	}

	if(this->viewport){
		delete []this->viewport;
		this->viewport = NULL;
	}
}



void Selection::set_config( float *_pts, int _nr, float* _left_bottom, float* _right_top, float* _model_view, float* _proj, int *_viewport, int _stride, int _offset )
{
	pts = _pts;
	nr = _nr;
	offset = _offset;
	stride = _stride;
	
	memcpy(left_bottom, _left_bottom, sizeof(float) * 2);
	memcpy(right_top, _right_top, sizeof(float)* 2);


	memcpy(model_view, _model_view, sizeof(float) * 16);
	memcpy(proj, _proj, sizeof(float) * 16);
	memcpy(viewport, _viewport, sizeof(int) * 4);

	/*** 计算被选中的index ***/

	cal_selected_index();
}

/***
   |-offset-|
    r  g  b  x  y  z 
   |-----stride-----|
***/
void Selection::cal_selected_index()
{
	vec_selected_pts_index.clear();

	int i = 0;
	for(i = 0; i != nr; i += 1){

		if( drop_in_area(pts + i * stride + offset) ){
			vec_selected_pts_index.push_back(i);
		} 

	}

}

bool Selection::drop_in_area( float* x )
{
	float win_coord[2];

	projectXY(win_coord, model_view, proj, viewport, x);

	if( (win_coord[0] < left_bottom[0] && win_coord[0] <right_top[0]) || (win_coord[0] > left_bottom[0] && win_coord[0] > right_top[0] ))
		return false;

	if( (win_coord[1] < left_bottom[1] && win_coord[1] <right_top[1]) || (win_coord[1] > left_bottom[1] && win_coord[1] > right_top[1] ))
		return false;

	return true;
}

void Selection::projectXY( float* win_coord, float* modelview, float* _proj, int* viewport, float* pos )
{
	float vback[4], vforth[4];
	memcpy(vback, pos, sizeof(float) * 3);
	vback[3] = 1.0;

	matrixTransform(vforth, vback, modelview);
	matrixTransform(vback, vforth, _proj);

	if(!( vback[3] >= 0.0 && vback[3] <= 0.00001 ) ){
		vback[0] /= vback[3];
		vback[1] /= vback[3];
		vback[2] /= vback[3];
	}

	win_coord[0] = viewport[0] + (1.0 + vback[0]) * viewport[2] / 2;
	win_coord[1] = viewport[1] + (1.0 + vback[1]) * viewport[3] / 2;
}

void Selection::matrixTransform( float* vOut, float* v, float* m )
{
	vOut[0] = m[0] * v[0] + m[4] * v[1] + m[8] *  v[2] + m[12] * v[3];	 
	vOut[1] = m[1] * v[0] + m[5] * v[1] + m[9] *  v[2] + m[13] * v[3];	
	vOut[2] = m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3];	
	vOut[3] = m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3];
}



void Selection::get_selected_index( int *vec_idx )
{
	int size = this->vec_selected_pts_index.size();

	for(int i = 0; i < size; i++){
		vec_idx[i] = this->vec_selected_pts_index[i];
	}
}

int Selection::get_selected_index_size()
{
	return this->vec_selected_pts_index.size();
}




#include <sys/time.h>
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <netdb.h>
#include <string.h>
#include <time.h>
#include <pthread.h>


#define PACKET_SIZE 4096
int datalen = 56;
unsigned short cal_chksum(unsigned short *, int );
int   pack(int , int , char* );
void  send_one_packet(int , char* , int , int , int , struct sockaddr_in );
void  tv_sub(struct timeval *out,struct timeval *in);
void  recv_packet(int *, int , int *, float *, int* ,  float, int );
double unpack(char *,int, struct timeval *, int, int );
void error_log(char *msg);


struct RecvPara{
    int *sockfds;
    int sock_size;
    int *loss;
    float *delay;
    int *icmpid;
    float timeout;
    int c;
};





void error_log(char *msg)
{       
        char path[1024];
        struct tm *today;
        time_t t;
        time(&t);
        today = localtime(&t);
        sprintf(path, "/home/qspace/log/hx_ping_module_%d%02d%d.log", today->tm_year + 1900, today->tm_mon + 1, today->tm_mday);
        
        FILE *log = fopen(path, "a+");
        fprintf(log,  msg); 
        fclose( log );
}


/*У����㷨*/
unsigned short cal_chksum(unsigned short *addr,int len)
{       int nleft=len;
        int sum=0;

        unsigned short *w=addr;
        unsigned short answer=0;
        
/*��ICMP��ͷ������������2�ֽ�Ϊ��λ�ۼ�����*/
        while(nleft>1)
        {       sum+=*w++;
                nleft-=2;
        }
        /*��ICMP��ͷΪ�������ֽڣ���ʣ�����һ�ֽڡ������һ���ֽ���Ϊһ��2�ֽ����ݵĸ��ֽڣ����2�ֽ����ݵĵ��ֽ�Ϊ0�������ۼ�*/
        if( nleft==1)
        {       *(unsigned char *)(&answer)=*(unsigned char *)w;
                sum+=answer;
        }
        sum=(sum>>16)+(sum&0xffff);
        sum+=(sum>>16);
        answer=~sum;
        return answer;
}


/*����ICMP��ͷ*/
int pack(int pack_no, int icmp_id1, char * send_packet)
{       
        int i,packsize;
        struct icmp *icmp;
        struct timeval *tval;
        icmp=(struct icmp*)send_packet;
        icmp->icmp_type=ICMP_ECHO;
        icmp->icmp_code=0;
        icmp->icmp_cksum=0;
        icmp->icmp_seq=pack_no;
        icmp->icmp_id=icmp_id1;
        packsize = 8+datalen;
        
        tval= (struct timeval *)icmp->icmp_data;
        gettimeofday(tval,NULL);    /*��¼����ʱ��*/
        icmp->icmp_cksum=cal_chksum( (unsigned short *)icmp,packsize); /*У���㷨*/
        return packsize;
}

/*��������ICMP����*/
void send_one_packet(int sockfd, char* send_packet, int packet_size, int pack_no, int icmp_id1, struct sockaddr_in dest_addr)
{       
        int real_len;
        real_len  =  pack(pack_no, icmp_id1, send_packet); /*����ICMP��ͷ*/
        sendto(sockfd, send_packet, real_len, 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr) );
}

/*��������ICMP����*/
void  recv_packet(int *sockfd, int sock_size, int *loss, float* delay, int* icmp_id1,  float timeout, int c)
{
        int n, fromlen, ret, i;
       
        float last_time = timeout;

        struct timeval begin;
        struct timeval end;
        
        struct timeval tvreceived;
        struct sockaddr from;

        char recvpacket[PACKET_SIZE];
        double unpack_ret;
        long last_sec;
        long last_usec;
        
        while(1)
        {
            gettimeofday(&begin, NULL);
            
            struct timeval tv_timeout;
            last_sec = last_time;
            last_usec = (last_time - last_sec) * 1000000.0;
            tv_timeout.tv_sec = last_time;
            tv_timeout.tv_usec = last_usec;
            
            
            fd_set read_conn;
            FD_ZERO(&read_conn);
            
            int max_fd = 0;
             
            for(i = 0; i < sock_size; i++){ 
                if( sockfd[i] >= 0 ){
                    if( sockfd[i] > max_fd ){
                        
                        max_fd = sockfd[i];

                    }
                    FD_SET(sockfd[i], &read_conn);
                }
            }
            
            ret = select(max_fd + 1, &read_conn, NULL, NULL, &tv_timeout);

            gettimeofday(&tvreceived, NULL);
            
            if( ret > 0 )
            {
                
                    for(i = 0; i < sock_size; i++)
                    {
                        if( sockfd[i] < 0)
                        {
                            continue;
                        }
                                    
                        if( FD_ISSET(sockfd[i], &read_conn) )
                        {
                            
                            n = recvfrom(sockfd[i], recvpacket,sizeof(recvpacket),0, (struct sockaddr *)&from, &fromlen);
                            
                            if(n == 0) 
                            {
                                loss[i]++;
                                sockfd[i] = -1;
                                continue;
                            }
                            
                            unpack_ret = unpack(recvpacket, n, &tvreceived, icmp_id1[i], c);
                            if( unpack_ret < 0 )
                            {   
                                continue;
                            }
                            else
                            {   
                                delay[i] += unpack_ret;
                                sockfd[i] = -2;
                            }
                        }
                   }
           }

           gettimeofday(&end, NULL);
           tv_sub(&end, &begin);
           last_time -= end.tv_sec+end.tv_usec/1000000.0;
           if(last_time <= 0 ||  ret == 0)
           {
                for(i = 0; i < sock_size; i++)
                {
                    if( sockfd[i] > 0)
                    {
                        loss[i]++;
                    }
                }
                break;
           }
      }
}


/*��ȥICMP��ͷ*/
double unpack(char *buf, int len, struct timeval *tvrecv, int icmp_id1, int c)
{       
    
        int i,iphdrlen;
        struct ip *ip;
        struct icmp *icmp;
        struct timeval *tvsend;
        double rtt;
        ip=(struct ip *)buf;
        iphdrlen=ip->ip_hl<<2;    /*��ip��ͷ����,��ip��ͷ�ĳ��ȱ�־��4*/
        icmp=(struct icmp *)(buf+iphdrlen);  /*Խ��ip��ͷ,ָ��ICMP��ͷ*/
        len-=iphdrlen;            /*ICMP��ͷ��ICMP���ݱ����ܳ���*/
        if( len<8 ) {               /*С��ICMP��ͷ�����򲻺���*/
                return -1;
        }
        /*ȷ�������յ����������ĵ�ICMP�Ļ�Ӧ*/
        if( (icmp->icmp_type==ICMP_ECHOREPLY) && (icmp->icmp_id==icmp_id1) && (icmp->icmp_seq==c))
        {      
                 
                tvsend=(struct timeval *)icmp->icmp_data;
                tv_sub(tvrecv,tvsend);  /*���պͷ��͵�ʱ���*/
                rtt=tvrecv->tv_sec*1000+tvrecv->tv_usec/1000.0;  /*�Ժ���Ϊ��λ����rtt*/
                /*��ʾ�����Ϣ*/
                return rtt;
        }
        else
        {
            return -1;
        }     
}

void *thread_recv_packet(void *d);


void *thread_recv_packet(void *d)
{

        struct RecvPara *p = (struct RecvPara*)d;

        
        int *sockfds_cp = (int*)malloc( sizeof(int) * p->sock_size);
        memcpy(sockfds_cp, p->sockfds, sizeof(int) * p->sock_size);

        recv_packet(sockfds_cp, p->sock_size,p->loss, p->delay,p->icmpid, p->timeout,p->c);

        free( sockfds_cp );
}


int main(int argc,   char *argv[])
{       
        if( argc < 5){
            printf("%s ip_num ping_count timeout . . .\n", argv[0]);
            return 0;
        }

        int MAX_PING_COUNT = atoi( argv[2] );

        
        int sock_size = atoi( argv[1] );
        
        struct hostent *host;
        struct protoent *protocol;
        unsigned long inaddr=0l;
        float timeout = atof( argv[3] ) ;
        
        int size=50*1024*1024;
        
        if( (protocol=getprotobyname("icmp") )==NULL)
        {       perror("getprotobyname");
                return -1;
        }

    
        /* ����rootȨ��,���õ�ǰ�û�Ȩ��*/
        setuid(getuid());
   
        int *sockfds = (int *)malloc( sizeof(int) * sock_size);
        
        struct sockaddr_in *dest_addrs = (struct sockaddr_in*) malloc( sizeof(struct sockaddr_in) * sock_size );
        
        int *icmpid = (int*)malloc( sizeof(int) * sock_size);
        
        int pid=getpid(), i, c;
        for(i = 0; i < sock_size; i++){

        /*����ʹ��ICMP��ԭʼ�׽���,�����׽���ֻ��root��������*/
            if( (sockfds[i] = socket(AF_INET,SOCK_RAW,protocol->p_proto) )<0)
            {       perror("socket error");
                    return -1;
            }
            
            /*�����׽��ֽ��ջ�������50K��������ҪΪ�˼�С���ջ����������
              �Ŀ�����,��������pingһ���㲥��ַ��ಥ��ַ,������������Ӧ��*/
            
            setsockopt(sockfds[i], SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));
            bzero( &dest_addrs[i], sizeof(struct sockaddr_in) );
            dest_addrs[i].sin_family=AF_INET;
            /*�ж�������������ip��ַ*/
            
            if( (inaddr=inet_addr( argv[i + 4] ))  == INADDR_NONE)
            {       if((host=gethostbyname(argv[i + 4]) )==NULL) /*��������*/
                    {       perror("gethostbyname error");
                            return -1;
                    }
                    memcpy( (char *)&dest_addrs[i].sin_addr,host->h_addr,host->h_length);
            }
            else {
                   /*��ip��ַ*/
                    dest_addrs[i].sin_addr.s_addr = inaddr;
            }
            /*��ȡmain�Ľ���id,��������ICMP�ı�־��*/
          
            icmpid[i] =  i;
       
       }
        
        char send_packet[PACKET_SIZE];
        
        int *loss = (int*)malloc( sizeof(int) * sock_size);
        float *delay = (float*)malloc( sizeof(float) * sock_size);
        
        bzero(loss, sizeof(int) * sock_size);
        bzero(delay, sizeof(float) * sock_size);
            

        pthread_t thread_pid;
        struct RecvPara paras;
        
        for(c = 0; c < MAX_PING_COUNT; c++){
           
            paras.sockfds = sockfds;
            paras.sock_size = sock_size;
            paras.loss = loss;
            paras.delay = delay;
            paras.icmpid = icmpid;
            paras.timeout = timeout;
            paras.c = c;
            
            pthread_create(&thread_pid, NULL, thread_recv_packet, (void*)&paras);
            
            for(i = 0; i < sock_size; i++){
                send_one_packet( sockfds[i], send_packet, PACKET_SIZE, c, icmpid[i], dest_addrs[i] ); 
            }
            
            pthread_join( thread_pid, NULL );
        }
        
        
        for(i = 0; i < sock_size; i++){

            if(loss[i] != MAX_PING_COUNT){
                
                printf("%s %d %d\n", argv[i+4],\
                (int)(10000 * loss[i] * 1.0 / MAX_PING_COUNT),(int)(1000 *  delay[i] / (MAX_PING_COUNT - loss[i]) ));
                
            }else{
                
                printf("%s %d %d\n", argv[i + 4], (int)(10000 * loss[i] * 1.0 / MAX_PING_COUNT), 0);
            }
        }
        
        for(i = 0; i < sock_size; i++){

            close(sockfds[i]);

        }
        free( dest_addrs );
        free( loss );
        free( delay );
        free( sockfds );
        free( icmpid );
        return 0;
}


/*����timeval�ṹ���*/
void tv_sub(struct timeval *out,struct timeval *in)
{       if( (out->tv_usec-=in->tv_usec)<0)
        {       --out->tv_sec;
                out->tv_usec+=1000000;
        }
        out->tv_sec-=in->tv_sec;
}
/*------------- The End -----------*/
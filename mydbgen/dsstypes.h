/*
* $Id: dsstypes.h,v 1.3 2005/10/28 02:57:04 jms Exp $
*
* Revision History
* ===================
* $Log: dsstypes.h,v $
* Revision 1.3  2005/10/28 02:57:04  jms
* allow for larger names in customer table
*
* Revision 1.2  2005/01/03 20:08:58  jms
* change line terminations
*
* Revision 1.1.1.1  2004/11/24 23:31:46  jms
* re-establish external server
*
* Revision 1.3  2004/04/07 20:17:29  jms
* bug #58 (join fails between order/lineitem)
*
* Revision 1.2  2004/01/22 05:49:29  jms
* AIX porting (AIX 5.1)
*
* Revision 1.1.1.1  2003/08/07 17:58:34  jms
* recreation after CVS crash
*
* Revision 1.2  2003/08/07 17:58:34  jms
* Convery RNG to 64bit space as preparation for new large scale RNG
*
* Revision 1.1.1.1  2003/04/03 18:54:21  jms
* initial checkin
*
*
*/
 /* 
 * general definitions and control information for the DSS data types
 * and function prototypes
 */

/*
 * typedefs
 */
typedef struct
{
    DSS_HUGE            custkey;
    char            name[C_NAME_LEN + 3];
    char            address[C_ADDR_MAX + 1];
    int             alen;
    DSS_HUGE            nation_code;
    char            phone[PHONE_LEN + 1];
    DSS_HUGE            acctbal;
    char            mktsegment[MAXAGG_LEN + 1];
    char            comment[C_CMNT_MAX + 1];
    int             clen;
}               customer_t;
/* customers.c */
long mk_cust   PROTO((DSS_HUGE n_cust, customer_t * c));
int pr_cust    PROTO((customer_t * c, int mode));
int ld_cust    PROTO((customer_t * c, int mode));

typedef struct
{
    DSS_HUGE	    okey; 
    DSS_HUGE            partkey;
    DSS_HUGE            suppkey;
    DSS_HUGE            lcnt;
    DSS_HUGE            quantity;
    DSS_HUGE            eprice;
    DSS_HUGE            discount;
    DSS_HUGE            tax;
    char            rflag[1];
    char            lstatus[1];
    char            cdate[DATE_LEN];
    char            sdate[DATE_LEN];
    char            rdate[DATE_LEN];
    char           shipinstruct[MAXAGG_LEN + 1];
    char           shipmode[MAXAGG_LEN + 1];
    char           comment[L_CMNT_MAX + 1];
    int            clen;
}               line_t;



typedef struct
{
    DSS_HUGE            lcnt;
    DSS_HUGE            quantity;
    DSS_HUGE            eprice;
    DSS_HUGE            discount;
    DSS_HUGE            tax;
    char            rflag[1];
    char            lstatus[1];
    char            cdate[DATE_LEN];
    char            sdate[DATE_LEN];
    char            rdate[DATE_LEN];
    char           shipinstruct[MAXAGG_LEN + 1];
    char           shipmode[MAXAGG_LEN + 1];
    char           comment[L_CMNT_MAX + 1];
    int            clen;

    //order
    DSS_HUGE	    orderkey; //okey
    char            orderstatus;
    DSS_HUGE        ordertotalprice;
    char            orderdate[DATE_LEN];
    char            orderpriority[MAXAGG_LEN + 1];
    char            orderclerk[O_CLRK_LEN + 1];
    long            orderspriority;
    char            ordercomment[O_CMNT_MAX + 1];
    int             orderclen;

    //customer
    DSS_HUGE        custkey;
    char            custname[C_NAME_LEN + 3];
    char            custaddress[C_ADDR_MAX + 1];
    int             custalen;
    DSS_HUGE        custnation_code;
    char            custphone[PHONE_LEN + 1];
    DSS_HUGE        custacctbal;
    char            custmktsegment[MAXAGG_LEN + 1];
    char            custcomment[C_CMNT_MAX + 1];
    int             custclen;

    //supplier
    DSS_HUGE        suppkey;
    char            suppname[S_NAME_LEN + 1];
    char            suppaddress[S_ADDR_MAX + 1];
    int             suppalen;
    DSS_HUGE        suppnation_code;
    char            suppphone[PHONE_LEN + 1];
    DSS_HUGE        suppacctbal;
    char            suppcomment[S_CMNT_MAX + 1];
    int             suppclen;

    //part
    DSS_HUGE       partkey;
    char           partname[P_NAME_LEN + 1];
    int            partnlen;
    char           partmfgr[P_MFG_LEN + 1];
    char           partbrand[P_BRND_LEN + 1];
    char           parttype[P_TYPE_LEN + 1];
    int            parttlen;
    DSS_HUGE       partsize;
    char           partcontainer[P_CNTR_LEN + 1];
    DSS_HUGE       partretailprice;
    char           partcomment[P_CMNT_MAX + 1];
    int            partclen;
    DSS_HUGE       partsuppqty;
    DSS_HUGE       partsuppcost;
    char           partsuppcomment[PS_CMNT_MAX + 1];
    int            partsupplen;

    DSS_HUGE        custnationkey;
    char            custnationname[20];
    char            custnationcomment[N_CMNT_MAX + 1];
    int             custnationclen;

    DSS_HUGE        custregionkey;
    char            custregionname[20];
    char            custregioncomment[N_CMNT_MAX + 1];
    int             custregionclen;

    DSS_HUGE        suppnationkey;
    char            suppnationname[20];
    char            suppnationcomment[N_CMNT_MAX + 1];
    int             suppnationclen;

    DSS_HUGE        suppregionkey;
    char            suppregionname[20];
    char            suppregioncomment[N_CMNT_MAX + 1];
    int             suppregionclen;

}               line_t_2;

typedef struct
{
    DSS_HUGE	    okey;
    DSS_HUGE        custkey;
    char            orderstatus;
    DSS_HUGE            totalprice;
    char            odate[DATE_LEN];
    char            opriority[MAXAGG_LEN + 1];
    char            clerk[O_CLRK_LEN + 1];
    long            spriority;
    DSS_HUGE            lines;
    char            comment[O_CMNT_MAX + 1];
    int            clen;
    line_t          l[1];
}               order_t;

/* order.c */
long	mk_order	PROTO((DSS_HUGE index, order_t * o, long upd_num));
int		pr_order	PROTO((order_t * o, int mode));
int		ld_order	PROTO((order_t * o, int mode));
void	mk_sparse	PROTO((DSS_HUGE index, DSS_HUGE *ok, long seq));

typedef struct
{
    DSS_HUGE            partkey;
    DSS_HUGE            suppkey;
    DSS_HUGE            qty;
    DSS_HUGE            scost;
    char           comment[PS_CMNT_MAX + 1];
    int            clen;
}               partsupp_t;

typedef struct
{
    DSS_HUGE           partkey;
    char           name[P_NAME_LEN + 1];
    int            nlen;
    char           mfgr[P_MFG_LEN + 1];
    char           brand[P_BRND_LEN + 1];
    char           type[P_TYPE_LEN + 1];
    int            tlen;
    DSS_HUGE           size;
    char           container[P_CNTR_LEN + 1];
    DSS_HUGE           retailprice;
    char           comment[P_CMNT_MAX + 1];
    int            clen;
    partsupp_t     s[1];
}               part_t;

/* parts.c */
long mk_part   PROTO((DSS_HUGE index, part_t * p));
int pr_part    PROTO((part_t * part, int mode));
int ld_part    PROTO((part_t * part, int mode));

typedef struct
{
    DSS_HUGE            suppkey;
    char            name[S_NAME_LEN + 1];
    char            address[S_ADDR_MAX + 1];
    int             alen;
    DSS_HUGE            nation_code;
    char            phone[PHONE_LEN + 1];
    DSS_HUGE            acctbal;
    char            comment[S_CMNT_MAX + 1];
    int             clen;
}               supplier_t;
/* supplier.c */
long mk_supp   PROTO((DSS_HUGE index, supplier_t * s));
int pr_supp    PROTO((supplier_t * supp, int mode));
int ld_supp    PROTO((supplier_t * supp, int mode));

typedef struct
{
    DSS_HUGE            timekey;
    char            alpha[DATE_LEN];
    long            year;
    long            month;
    long            week;
    long            day;
} dss_time_t;               

/* time.c */
long mk_time   PROTO((DSS_HUGE h, dss_time_t * t));

/*
 * this assumes that N_CMNT_LEN >= R_CMNT_LEN 
 */
typedef struct
{
    DSS_HUGE            code;
    char            *text;
    long            join;
    char            comment[N_CMNT_MAX + 1];
    int             clen;
}               code_t;

/* code table */
int mk_nation   PROTO((DSS_HUGE i, code_t * c));
int pr_nation    PROTO((code_t * c, int mode));
int ld_nation    PROTO((code_t * c, int mode));
int mk_region   PROTO((DSS_HUGE i, code_t * c));
int pr_region    PROTO((code_t * c, int mode));
int ld_region    PROTO((code_t * c, int mode));


//long mk_my_line_item(DSS_HUGE index, line_t_2 * o, long upd_num);
long mk_my_line_item(DSS_HUGE index, line_t_2 * o, order_t * order, customer_t * customer, supplier_t * supplier, part_t * part,code_t * n,code_t * r,long upd_num);
void set_line_item_order(line_t_2 * line_item, order_t * order);
void set_line_item_customer(line_t_2 * line_item, customer_t * customer);
void set_line_item_supplier(line_t_2 * line_item, supplier_t * supplier);
void set_line_item_part(line_t_2 * line_item, part_t * part);
//int pr_mylineitem (line_t_2 * l, order_t * order, customer_t * customer, supplier_t * supplier, part_t * part, int mode);
int pr_mylineitem (line_t_2 * l, int mode);

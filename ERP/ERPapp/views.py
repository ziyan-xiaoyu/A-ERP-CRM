import math
import datetime
from django import forms
from django.shortcuts import render, redirect
from django.template.defaulttags import register  # 导入Django自定义函数
from ERPapp import models


# Create your views here.
def index(request):
    """首页 选择"""
    return render(request, 'index.html')


class MPSModelForm(forms.ModelForm):
    """MPS数据提交的ModelForm"""
    class Meta:
        model = models.MPS
        fields = ["MPS_name", "MPS_num", "MPS_time"]


def MPS_list(request):
    """MPS数据提交"""
    models.MPS.objects.all().delete()  # 清空之前的查询记录
    if request.method == "GET":
        form = MPSModelForm()
        return render(request, 'mps.html', {"form": form})

    # 用户POST提交数据，校验(解决了用户提交的数据没有进行校验的问题)
    form = MPSModelForm(data=request.POST)
    if form.is_valid():
        # 数据合法则保存到数据库
        # print(form.data)
        form.save()
        return redirect('/index/plan/')

    # 校验失败（在页面上显示错误信息）
    # print(form.errors)
    return render(request, 'mps.html', {"form": form})


@register.filter  # 加入自定义函数(过滤器)range 因为django中没有range函数
def get_range(value):
    return range(value)


def Plan_list(request):
    """MPS计算 显示采购计划和生产计划"""
    # 从数据库中提取所有表的数据
    bom = models.BOM.objects.all()
    materiel = models.Materiel.objects.all()
    allo = models.Allocation.objects.all()
    cash = models.Cash.objects.all()
    mps_f = models.MPS.objects.filter()

    # 在数据表中获取对应列的数据
    MPS_name = []  # 成品名称
    MPS_num = []  # 成品需求量
    MPS_time = []  # 完工日期
    for obj in mps_f:
        MPS_name = obj.MPS_name
        MPS_num = obj.MPS_num
        MPS_time = obj.MPS_time

    part_quantity = []  # 装配个数
    level_2 = 0  # 层次为2的物料数
    for obj in bom:
        part_quantity.append(obj.part_quantity)
        if obj.part_level == 2:
            level_2 = level_2 + 1

    m_way = []  # 调配方式
    m_num = []  # 物料号
    m_name = []  # 物料名称
    m_wastage = []  # 损耗率
    work_time = []  # 作业提前期
    for obj in materiel:
        m_way.append(obj.get_m_way_display())
        m_num.append(obj.m_num)
        m_name.append(obj.m_name)
        m_wastage.append(obj.m_wastage)
        work_time.append(obj.work_time)

    materiel_time = []  # 配料提前期(len = 7)
    manufacture_time = []  # 供应商提前期(len = 7)
    materiel_time.append(0)  # 将列表长度变为8位
    manufacture_time.append(0)  # 将列表长度变为8位
    for obj in allo:
        materiel_time.append(obj.materiel_time)
        manufacture_time.append(obj.manufacture_time)

    operation_c = []  # 工序库存
    materiel_c = []  # 资材库存
    for obj in cash:
        operation_c.append(obj.operation_c)
        materiel_c.append(obj.materiel_c)

    # 计算：循环次数 返回列表的行数
    list_num = 0
    if MPS_name == '眼镜':
        list_num = len(part_quantity)
    elif MPS_name == '镜框':
        list_num = level_2 + 1
    print(list_num)

    # 判断产品种类  计算需求量 = 装配个数*父物料需求量/（1-损耗率） - 工序库存 - 资材库存
    need_num = {}  # 需求量 注意不能用[]，这是用列表装了字典的内容
    if MPS_name == '眼镜':
        for i in get_range(list_num):
            need_num[i] = math.ceil(part_quantity[i] * MPS_num / (1 - m_wastage[i]) - operation_c[i] - materiel_c[i])
    elif MPS_name == '镜框':
        for i in get_range(list_num):
            need_num[i] = math.ceil(
                part_quantity[i + 1] * MPS_num / (1 - m_wastage[i + 1]) - operation_c[i + 1] - materiel_c[i + 1])

    # 判断产品种类  计算下达/完成日期 下达日期 = 完成日期 - 作业提前期 - 配料提前期 - 供应商提前期
    # 注：换算完工日期的方法：relativedelta 函数模块导入不成功，换用datetime.timedelta()
    mps_time = datetime.datetime.strptime(str(MPS_time), '%Y-%m-%d')
    start_time = {}  # 日程下达时间
    bingo_time = {}  # 日程完成日期
    if MPS_name == '眼镜':
        for i in get_range(list_num):
            if i == 0:  # 成品/树根
                bingo_time[i] = mps_time
                start_time[i] = bingo_time[i] - datetime.timedelta(days=work_time[i])
            elif i == 1 or i == 6 or i == 7:  # 父物料/树的第一层
                bingo_time[i] = start_time[0]
                start_time[i] = bingo_time[i] - datetime.timedelta(
                    days=(work_time[i] + materiel_time[i] + manufacture_time[i]))
            else:  # 子物料/树的第二层
                bingo_time[i] = start_time[1]
                start_time[i] = bingo_time[i] - datetime.timedelta(
                    days=(work_time[i] + materiel_time[i] + manufacture_time[i]))
    elif MPS_name == '镜框':
        for i in get_range(list_num):
            if i == 0:  # 成品/父物料/树根
                bingo_time[i] = mps_time
                start_time[i] = bingo_time[i] - datetime.timedelta(days=work_time[i + 1])
            else:  # 子物料/树的第一层
                bingo_time[i] = start_time[0]
                start_time[i] = bingo_time[i] - datetime.timedelta(
                    days=(work_time[i + 1] + materiel_time[i + 1] + manufacture_time[i + 1]))

    # 制作返回的列表
    plan_list = []  # 传递给前端的采购计划和生产计划表
    for i in get_range(list_num):
        if MPS_name == '眼镜':
            list_i = [m_way[i], m_num[i], m_name[i], need_num[i], start_time[i].strftime('%Y-%m-%d'),
                      bingo_time[i].strftime('%Y-%m-%d')]
            plan_list.append(list_i)
        elif MPS_name == '镜框':
            list_i = [m_way[i + 1], m_num[i + 1], m_name[i + 1], need_num[i], start_time[i].strftime('%Y-%m-%d'),
                      bingo_time[i].strftime('%Y-%m-%d')]
            plan_list.append(list_i)

    # 将列表按照下达日期由早到晚排序
    for i in get_range(list_num - 1):
        for j in get_range(list_num - 1 - i):
            if plan_list[j][4] > plan_list[j + 1][4]:
                temp = plan_list[j + 1]
                plan_list[j + 1] = plan_list[j]
                plan_list[j] = temp

    return render(request, 'mps.html', {"plan_list": plan_list, "msg": "提交成功"})


class BalanceModelForm(forms.ModelForm):
    """资产负债表数据提交的ModelForm"""
    class Meta:
        model = models.Asset
        fields = ["asset_name"]


def Balance_list(request):
    """资产负债数据提交与计算"""
    models.Asset.objects.all().delete()  # 清空之前的查询记录
    if request.method == "GET":
        form = BalanceModelForm()
        return render(request, 'balance.html', {"form": form})

    # 用户POST提交数据，校验(解决了用户提交的数据没有进行校验的问题)
    form = BalanceModelForm(data=request.POST)
    if form.is_valid():
        # 数据合法则保存到数据库
        form.save()
        return redirect('/index/count/')

    return render(request, 'balance.html', {"form": form})


def Count_list(request):
    """资产负债计算 显示公式"""
    # 从数据库中提取所有表的数据
    balance = models.Balance.objects.all()
    asset = models.Asset.objects.filter()

    # 在数据表中获取对应列的数据
    u_name = []   # 需要查找的变量名
    for obj in asset:
        u_name = obj.asset_name

    u_name_id = []   # 需要查找的变量名对应的id
    for obj in balance:
        if obj.asset_name == u_name:
            u_name_id = obj.id

    o_name = []   # 找出包含的变量集合
    for obj in balance:
        if obj.guid_num == u_name_id:
            o_name.append(obj.asset_name)

    # 将变量集合转换成字符串公式
    formula = str(u_name) + '='
    for i in get_range(len(o_name)):
        if i == 0:
            formula = formula + str(o_name[i])
        else:
            formula = formula + '+' + str(o_name[i])

    return render(request, 'balance.html', {"formula": formula, "u_name": u_name, "msg": "提交成功"})

from django.db import models


# Create your models here.

# BOM表
class BOM(models.Model):
    """BOM表"""
    part_num = models.IntegerField(verbose_name="零件号")
    part_name = models.CharField(verbose_name="零件描述", max_length=32)
    part_quantity = models.IntegerField(verbose_name="装配个数")
    part_level = models.IntegerField(verbose_name="所属层次")


# 物料表
class Materiel(models.Model):
    """物料表"""
    m_num = models.IntegerField(verbose_name="物料号")
    m_name = models.CharField(verbose_name="物料名称", max_length=32)
    way_choices = (
        (1, "生产"),
        (2, "采购"),
    )
    m_way = models.SmallIntegerField(verbose_name="调配方式", choices=way_choices)
    m_wastage = models.DecimalField(verbose_name="损耗率", max_digits=3, decimal_places=2)
    work_time = models.IntegerField(verbose_name="作业提前期(/天)")


# 调配构成表
class Allocation(models.Model):
    """调配构成表"""
    a_num = models.IntegerField(verbose_name="调配基准编号")
    a_code = models.CharField(verbose_name="调配区代码", max_length=32)

    father_m = models.ForeignKey(verbose_name="父物料", to="Materiel", related_name="father_m", on_delete=models.CASCADE)
    child_m = models.ForeignKey(verbose_name="子物料", to="Materiel", related_name="child_m", on_delete=models.CASCADE)
    # fa_num = models.ForeignKey(verbose_name="父物料号", to="Materiel", to_field="m_num", on_delete=models.CASCADE)
    # fa_name = models.ForeignKey(verbose_name="父物料名称", to="Materiel", to_field="m_name", on_delete=models.CASCADE)
    # ch_num = models.ForeignKey(verbose_name="子物料号", to="Materiel", to_field="m_num", on_delete=models.CASCADE)
    # ch_name = models.ForeignKey(verbose_name="子物料名称", to="Materiel", to_field="m_name", on_delete=models.CASCADE)

    materiel_time = models.IntegerField(verbose_name="配料提前期(/天)")
    manufacture_time = models.IntegerField(verbose_name="供应商提前期(/天)")


# 库存表
class Cash(models.Model):
    """库存表"""
    cash_m = models.ForeignKey(verbose_name="库存物料", to="Materiel", on_delete=models.CASCADE)
    # c_num = models.ForeignKey(verbose_name="物料号", to="Materiel", to_field="m_num", on_delete=models.CASCADE)
    # c_name = models.ForeignKey(verbose_name="物料名称", to="Materiel", to_field="m_name", on_delete=models.CASCADE)
    operation_c = models.IntegerField(verbose_name="工序库存")
    materiel_c = models.IntegerField(verbose_name="资材库存")


# MPS记录
class MPS(models.Model):
    """每条MPS记录"""
    MPS_name = models.CharField(verbose_name="产品名称", max_length=32)
    MPS_num = models.IntegerField(verbose_name="数量")
    MPS_time = models.DateField(verbose_name="完工日期")


# 资产负债表
class Balance(models.Model):
    """资产负债表"""
    description = models.TextField(verbose_name="资产类说明")
    guid_mark = models.CharField(verbose_name="资产类方向", max_length=16, null=True)
    guid_num = models.IntegerField(verbose_name="资产类汇总序号", null=True)
    asset_name = models.CharField(verbose_name="变量名", max_length=32, null=True)


# balance 变量记录
class Asset(models.Model):
    """每次查询的变量记录"""
    asset_name = models.CharField(verbose_name="变量名", max_length=32)
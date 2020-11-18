# model settings
model = dict(
    type='PPYOLODetector',
    pretrained='/disk2/project/pytorch-YOLOv4/checkpoints/resnet50.pth',
    backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(1, 2, 3),
        frozen_stages=1,
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=True,
        style='pytorch',
        dcn=dict(type='DCNv2', deformable_groups=1, fallback_on_stride=False),  # 可变形卷积配置
        # dcn=None,
        stage_with_dcn=(False, False, False, True)  # 只在最后阶段添加DCN
    ),
    neck=dict(
        type='PPFPN',
        in_channels=[512, 1024, 2048],
        coord_conv=True,
        drop_block=True,
        spp=True,
        second_drop_block=True,
        spp_kernel_sizes=[5, 9, 13],  # spp 核大小
        norm_type='BN',  # 支持BN，GN
        num_groups=None  # norm_type=GN 需要给出组大小，通道整数倍
    ),
    head=dict(
        type='PPHead',
        in_channels=[128, 256, 512],
        num_classes=5,
        label_smooth=True,
        coord_conv=True,
        deta=0.01,
        anchors=[[10, 13], [16, 30], [33, 23],
                 [30, 61], [62, 45], [59, 119],
                 [116, 90], [156, 198], [373, 326]],
        anchor_masks=[[6, 7, 8], [3, 4, 5], [0, 1, 2]],
        downsample_ratios=[32, 16, 8],
        nms_type='nms',  # Support types :nms or soft_nms
        nms_thr=.5,
        ignore_thre=.3,
        iou_aware_factor=0.4,
        scale_x_y=1.05,
        iou_aware=False,
        yolo_loss_type='yolov5',  # 损失函数类型支持，支持字段 yolov4，None，None为PP-YOLO损失函数支持
        xywh_loss=True,
        bbox_weight=False,  # 是否添加yolo系列bbox权重计算方法2.0-(1.0*gw*gh)/(h*w)
        conf_balances=[0.4, 1, 4],
        norm_type='BN',  # 支持BN，GN
        num_groups=None,  # norm_type=GN 需要给出组大小，通道整数倍
        bbox_loss=dict(type='IOU_Loss', iou_type='GIOU', loss_weight=0.05),
        confidence_loss=dict(type='Conf_Loss', pos_weight=1.0, loss_weight=1.),
        class_loss=dict(type='Class_Loss', loss_weight=0.5, pos_weight=0.5),
        aware_Loss=dict(type='IOU_Aware_Loss', loss_weight=0.5)
    )
)

# dataset settings
img_scale = 640  # 图片缩放尺度
train_pipeline = [
    dict(
        type='Mosaic',  # Mosaic
        img_scale=img_scale,
        transforms=[
            dict(type='LoadImageFromFile'),  # 从配置项加载图片和标签，真框等并对框进行归一化
            dict(type='Resize', img_scale=img_scale, letterbox=False),  # Resize图片，此处letterbox必须为False
        ]),
    dict(type='RandomAffine', degrees=0, translate=0, scale=.5, shear=0.0),  # 随机放射变换
    dict(type='RandomHSV'),  # 随机颜色抖动
    dict(type='RandomFlip'),  # 随机翻转
    dict(type='Normalize'),  # 格式化数据主要对输入图片格式化，归一化图片 /255
    dict(type='ImageToTensor'),  # 将图片numpy转换为torch 张量，并reshape为模型Input shape
    dict(type='Collect'),  # 过滤不需要的字典数据
]
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', img_scale=img_scale, letterbox=True, auto=True, scaleup=True),  # 图片resize到img_scale，并最小自适应宽高
    dict(type='Normalize'),
    dict(type='ImageToTensor'),
    dict(type='Collect', keys=['img']),
]

val_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', img_scale=img_scale, letterbox=True, auto=False, scaleup=False),  # 图片resize到img_scale，缺失部分用灰色填充
    dict(type='Normalize'),
    dict(type='ImageToTensor'),
    dict(type='Collect'),
]

data_root = '/home/cxj/Desktop/data/coco'
dataset_type = 'Custom'
data = dict(
    batch_size=64,
    subdivisions=16,
    workers_per_gpu=1,
    train=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file=data_root + '/annotations/train.txt',
        img_prefix='images/train2017',
        name_file='annotations/label.names',
        pipeline=train_pipeline
    ),
    val=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file=r'annotations/val.txt',
        img_prefix='images/val2017',
        name_file='annotations/label.names',
        pipeline=val_pipeline
    ),
    test=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file=data_root + 'annotations/test.txt',
        img_prefix='images/test2017',
        name_file='annotations/label.names',
        pipeline=test_pipeline
    )
)
# Model Exponential Moving Average
# https://www.tensorflow.org/api_docs/python/tf/train/ExponentialMovingAverage
ema = dict(decay=0.9999, updates=0)  # Exponential Moving Average 配置
# optimizer
optimizer = dict(type='SGD', lr=0.001, momentum=0.937, weight_decay=5e-4)  # 优化器 默认SGD
# 优化器配置项 grad_clip:梯度剪切，防止梯度爆炸或消失,
# detect_anomaly :该参数在debug模式下打开，可帮助调试代码，默认关闭，影响模型训练速度。
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2), detect_anomaly=False)
# learning policy
lr_config = dict(
    policy='cosine',
    warmup='linear',
    warmup_iters=15000,
    # warmup_by_epoch=True,
    warmup_ratio=1.0 / 3,
    target_lr=0.0002,
    # step=[8,12,18,22])
)
checkpoint_config = dict(interval=1)  # 模型保存策略，默认每个epoch都保存
# 日志配置
log_config = dict(
    interval=10,  # 多少个批次打印一条日志
    hooks=[
        dict(type='TextLoggerHook'),
        # dict(type='TensorboardLoggerHook')
    ])

evaluation = dict(interval=2, save_best=True)  # 验证集配置，根据统计指标计算，默认给保存最好的模型
total_epochs = 100  # 训练epoch大小
work_dir = '/disk2/project/pytorch-YOLOv4/work_dirs/yolov5_hand'  # 模型保存文件目录，包含日志文件
load_from = None  # 用于加载已训练完模型，用于用较低学习率微调网络
resume_from = None  # 用于程序以外中断，继续训练
workflow = [('train', 1)]  # 可添加('val', 1)，训练集和验证集一块参与训练

log_info = dict(
    # 日志保留路径,默认保留在项目跟目录下的logs文件
    log_dir='',
    # 日志级别,默认INFO级别,ERROR,WARNING,WARN,INFO,DEBUG
    log_level='INFO',
    # 每天生成几个日志文件,默认每天生成1个
    log_interval=1,
    # #日志保留多少天,默认保留7天的日志
    log_backupCount=7,
)

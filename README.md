# Student Data Pipeline

مشروع ETL متوسط المستوى لتنفيذ التكليف العملي الشامل في هندسة البيانات.

## 1. Project Overview

يقوم المشروع بجمع بيانات الطلاب من ثلاثة مصادر مختلفة:

1. CSV File
2. REST API محلي Mock
3. SQLite Database

ثم ينفذ:

**Extract → Validate → Clean → Integrate → Transform → Final Validate → Load**

والنتيجة النهائية:

- `data/processed/final_dataset.csv`
- `data/rejected/rejected_records.csv`
- `logs/pipeline.log`

## 2. Architecture

```text
CSV ───────┐
           │
REST API ──┼──> Extract ─> Clean/Validate ─> Integrate ─> Transform
           │                                             │
SQLite ────┘                                             ▼
                                                Final Validation
                                                   /        \
                                                  /          \
                                                 ▼            ▼
                                      final_dataset.csv   rejected_records.csv
```

تم فصل مصادر البيانات عن التنظيف والتحويل والتحقق حتى يمكن إضافة مصدر جديد مستقبلًا بدون إعادة كتابة كامل الـPipeline.

## 3. Data Sources

### CSV
الملف:
`data/raw/students.csv`

ويحتوي على:
- student_id
- student_name
- age
- major
- city

البيانات تحتوي عمدًا على مشاكل مثل التكرار والعمر غير الصحيح والقيم المفقودة والمسافات واختلاف حالة الأحرف.

### REST API
يتم تشغيل API محلي لتجنب الاعتماد على الإنترنت:

```bash
python mock_api.py
```

الرابط:
`http://127.0.0.1:8000/students`

ويعيد:
- student_id
- gpa
- attendance
- status

### SQLite
قاعدة البيانات:
`database/students.db`

وتحتوي على:
- courses
- enrollments

يتم استخراج بيانات المقررات والدرجات باستخدام SQL JOIN.

## 4. ETL Pipeline

### Extract
قراءة CSV، طلب REST API، وتنفيذ SQL على SQLite.

### Validate
التحقق من:
- student_id ليس NULL
- student_id غير مكرر
- age بين 16 و80
- GPA بين 0 و4
- attendance بين 0 و100
- score بين 0 و100

### Clean
- إزالة المسافات الزائدة.
- توحيد النصوص.
- تحويل أنواع البيانات.
- إزالة التكرارات.

### Integrate
دمج المصادر باستخدام `student_id`.

بيانات SQLite قد تحتوي عدة مقررات للطالب، لذلك يتم تجميعها لكل طالب وحساب متوسط الدرجة وعدد المقررات.

### Transform
تم إنشاء:
- `performance_level`
- `attendance_status`

#### performance_level
- GPA >= 3.5 → Excellent
- GPA >= 3.0 → Very Good
- GPA >= 2.5 → Good
- GPA >= 2.0 → Acceptable
- GPA < 2.0 → At Risk

#### attendance_status
- attendance >= 75 → Good
- attendance < 75 → Low

### Load
يتم حفظ البيانات الصحيحة في:
`data/processed/final_dataset.csv`

والبيانات المرفوضة في:
`data/rejected/rejected_records.csv`

## 5. Missing Values Strategy

- Missing GPA: استخدام median لقيم GPA المتوفرة.
- Missing Attendance: استخدام 0 كقاعدة عمل بسيطة تعني عدم وجود حضور مسجل.
- الحقول الاختيارية القادمة من SQLite يتم تعويضها بـ `Not Available` أو 0 حسب نوعها.

تم اختيار median للـGPA لأنه أقل تأثرًا بالقيم المتطرفة من المتوسط في البيانات الصغيرة.

## 6. Data Quality

السجلات التي تفشل في قواعد الجودة لا تدخل Dataset النهائي.

يتم تسجيل سبب الرفض في:
`error_reason`

مثال:
```text
1007,Invalid GPA,API
```

## 7. Installation

تأكد من وجود Python 3.10 أو أحدث.

```bash
pip install -r requirements.txt
```

ثم أنشئ قاعدة البيانات:

```bash
python database/create_database.py
```

## 8. Running

في نافذة Terminal الأولى:

```bash
python mock_api.py
```

ثم في نافذة Terminal ثانية:

```bash
python main.py
```

## 9. Testing

تم استخدام `unittest` من مكتبات Python القياسية.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

الاختبارات تغطي:
1. تحميل CSV.
2. إزالة التكرارات.
3. رفض البيانات غير الصحيحة.
4. التحقق من API data.
5. نجاح دمج المصادر.

## 10. Output

بعد تشغيل Pipeline:

### Final Dataset
`data/processed/final_dataset.csv`

Dataset نظيف ومتكامل وجاهز للتحليل.

### Rejected Records
`data/rejected/rejected_records.csv`

يحتوي السجلات التي فشلت في قواعد الجودة وسبب الرفض.

### Log
`logs/pipeline.log`

يسجل مراحل التنفيذ والإحصائيات.

## 11. Pipeline Metrics

يتم تسجيل:
- CSV Records
- API Records
- Database Records
- Integrated Records
- Valid Records
- Rejected Records
- Duplicate Records
- Missing Values
- Processing Time

## 12. أسئلة التكليف

### 1. لماذا نحتاج إلى Data Pipeline عند التعامل مع مصادر متعددة؟
لأن البيانات تكون موزعة بين مصادر مختلفة وبصيغ مختلفة، والـPipeline يوفر مسارًا منظمًا لاستخراجها وتوحيدها والتحقق منها ثم إنتاج Dataset واحد.

### 2. ما الفرق بين Raw Data وProcessed Data؟
Raw Data هي البيانات كما جاءت من المصدر قبل المعالجة، بينما Processed Data هي البيانات بعد التنظيف والتحويل والتحقق.

### 3. ما الفرق بين Extract وTransform وLoad؟
Extract استخراج البيانات، Transform تنظيف وتحويل وتجهيز البيانات، Load حفظ البيانات النهائية في الوجهة المطلوبة.

### 4. ما المشاكل التي واجهتها أثناء دمج البيانات؟
اختلاف جودة البيانات، التكرارات، القيم المفقودة، اختلاف تنسيق النصوص، ووجود أكثر من سجل مقرر للطالب في SQLite.

### 5. كيف تعاملت مع Missing Values؟
تم استخدام median للـGPA، و0 للحضور غير المسجل، وقيم افتراضية للبيانات الاختيارية.

### 6. كيف تعاملت مع Duplicate Records؟
تم كشف التكرار باستخدام `student_id` والاحتفاظ بأول سجل للطالب قبل مرحلة الدمج.

### 7. كيف تعاملت مع Invalid Records؟
تم تطبيق قواعد جودة واضحة، ثم حفظ السجلات المرفوضة في ملف مستقل مع سبب الرفض.

### 8. لماذا يجب فصل Extraction عن Transformation؟
لأن فصل المسؤوليات يجعل الكود أوضح وأسهل للاختبار، ويسمح بتغيير مصدر البيانات دون تغيير كامل مراحل المعالجة.

### 9. لماذا يعتبر Data Validation جزءًا أساسيًا؟
لمنع وصول البيانات الخاطئة إلى Dataset النهائي، وبالتالي تحسين موثوقية التحليل والتقارير والنماذج.

### 10. كيف يمكن تطوير Pipeline ليعمل بشكل دوري وآلي؟
يمكن تشغيله باستخدام Task Scheduler في Windows أو cron في Linux أو أداة orchestration مثل Airflow.

### 11. كيف يمكن جعل Pipeline يتعامل مع ملايين السجلات؟
باستخدام المعالجة على دفعات، القراءة المتدرجة، قواعد بيانات مناسبة، الفهارس، وتقليل تحميل البيانات إلى الذاكرة.

### 12. ما الفرق بين Batch Processing وStreaming؟
Batch يعالج مجموعة من البيانات على فترات، بينما Streaming يعالج البيانات أثناء وصولها بشكل مستمر أو شبه مستمر.

## 13. تطوير المشروع مستقبلًا

يمكن إضافة:
- Excel Source
- JSON Source
- MySQL
- PostgreSQL
- MongoDB
- ملف Configuration
- Incremental Processing
- Data Lineage
- نظام مراقبة Metrics أكثر تفصيلًا

# -*- coding: utf-8 -*-
"""
Титаник өгөгдлийн шинжилгээ - Алхам алхамын гарын авлага
Өгөгдлийн ухааны оюутнуудад зориулсан практик жишээ
"""

# Шаардлагатай сангуудыг импортлох
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Монгол фонт тохиргоо (хэрэв байгаа бол)
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['figure.figsize'] = (10, 6)

print("ТИТАНИК ӨГӨГДЛИЙН ШИНЖИЛГЭЭ - ПРАКТИК ЖИШЭЭ")
print("=" * 60)

# АЛХАМ 1: Өгөгдөл ачаалах
print("\nАЛХАМ 1: Өгөгдөл ачаалах")
print("-" * 30)

# Өгөгдлийн эх үүсвэр: локал файл -> URL -> жишээ өгөгдөл
TITANIC_URL = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv'

try:
    # Локал файлаас ачаалах (хамгийн хурдан)
    df = pd.read_csv('titanic.csv')
    print("Өгөгдөл локал titanic.csv файлаас ачаалагдлаа")
except FileNotFoundError:
    try:
        # Локал файл байхгүй тул URL-аас татаж, локал хадгалах
        df = pd.read_csv(TITANIC_URL)
        df.to_csv('titanic.csv', index=False)
        print(f"Өгөгдөл татаж авлаа -> lab/titanic.csv (дахин ачаалахад хурдан)")
    except Exception as url_error:
        print(f"URL-аас ч татаж чадсангүй ({url_error}).")
        print("https://www.kaggle.com/c/titanic/data")
        # Жишээ өгөгдөл үүсгэх
        np.random.seed(42)
        df = pd.DataFrame({
            'PassengerId': range(1, 101),
            'Survived': np.random.choice([0, 1], 100, p=[0.6, 0.4]),
            'Pclass': np.random.choice([1, 2, 3], 100, p=[0.2, 0.3, 0.5]),
            'Sex': np.random.choice(['male', 'female'], 100, p=[0.65, 0.35]),
            'Age': np.random.normal(30, 15, 100),
            'SibSp': np.random.poisson(0.5, 100),
            'Parch': np.random.poisson(0.3, 100),
            'Fare': np.random.lognormal(3, 1, 100),
            'Embarked': np.random.choice(['S', 'C', 'Q'], 100, p=[0.7, 0.2, 0.1])
        })
        print("Жишээ өгөгдөл үүсгэлээ")

print(f"Өгөгдлийн хэмжээ: {df.shape}")
print(f"Багануудын нэр: {list(df.columns)}")

# АЛХАМ 2: Анхдагч судалгаа
print("\nАЛХАМ 2: Анхдагч судалгаа")
print("-" * 30)

print("Өгөгдлийн ерөнхий мэдээлэл:")
print(df.info())

print("\nСтатистик үзүүлэлтүүд:")
print(df.describe())

print("\nХоосон утгууд:")
missing_data = df.isnull().sum()
print(missing_data[missing_data > 0])

# АЛХАМ 3: Өгөгдөл цэвэрлэгээ
print("\nАЛХАМ 3: Өгөгдөл цэвэрлэгээ")
print("-" * 30)

# --- 1) ЦОЛ (Title): Name-ээс устгахаас ӨМНӨ салгаж авах ---
if 'Name' in df.columns:
    df['Title'] = df['Name'].str.extract(r' ([A-Za-z]+)\.', expand=False)
    # Ховор цолуудыг нэгтгэх: цөөн бүлэгт медиан тогтворгүй байдаг
    rare_titles = ['Dr', 'Rev', 'Dona', 'Jonkheer', 'Countess', 'Lady', 'Sir',
                   'Col', 'Major', 'Don', 'Mme', 'Mlle', 'Ms', 'Capt']
    df['Title'] = df['Title'].replace(rare_titles, 'Rare')
    print("\nЦол бүрийн дундаж нас (медиан):")
    print(df.groupby('Title')['Age'].median().round(1))
    # Жишээ: Mr~30, Mrs~35, Miss~21, Master~4.5

# --- 2) НАС (Age): 3 шатлалт логик дүүргэлт ---
if 'Age' in df.columns and df['Age'].isnull().any():
    # Эхэндээ хоосон байсныг шинж болгон үлдээх (мэдээлэл өөрөө утгатай)
    df['Age_was_missing'] = df['Age'].isnull().astype(int)
    n_missing_age = int(df['Age_was_missing'].sum())
    # 1-р шат: Цолоор нөхөх (Master~4.5 нас, бүхэлд 28 биш!)
    df['Age'] = df.groupby('Title')['Age'].transform(lambda x: x.fillna(x.median()))
    # 2-р шат: Цол дотроо бүгд хоосон бол -> Хүйс + Ангиар
    df['Age'] = df.groupby(['Sex', 'Pclass'])['Age'].transform(lambda x: x.fillna(x.median()))
    # 3-р шат: үлдсэн бол -> нийт медиан (эцсийн бөмбөгөр)
    df['Age'] = df['Age'].fillna(df['Age'].median())
    print(f"Age: {n_missing_age} хоосон утгыг цол/бүлгээр нөхлөө "
          f"(Age_was_missing шинж нэмэгдлээ)")

# --- 3) СУУЛТЫН БУУДАЛ (Embarked): Анги + Тасалбарын үнээр шалтгаанлах ---
if 'Embarked' in df.columns and df['Embarked'].isnull().any():
    print("\n1-р ангийнхны буудлаар тасалбарын үнийн медиан:")
    print(df[df['Pclass'] == 1].groupby('Embarked')['Fare'].median().round(1))
    # Жишээ: C≈78, Q≈90, S≈52 -> 1-р анги + ~80$ төлсөн хүн C (Cherbourg)-оос суусан
    cond = df['Embarked'].isnull() & (df['Pclass'] == 1) & (df['Fare'] >= 70)
    df.loc[cond, 'Embarked'] = 'C'
    # Fallback: үлдсэн хоосон утга -> нийт хамгийн түгээмэл буудал
    df['Embarked'] = df['Embarked'].fillna(df['Embarked'].mode()[0])
    print("Embarked багананы хоосон утгыг Анги/Үнээр нөхлөө")

# --- 4) КАБИН (Cabin) -> ДЭЭВЭР (Deck): 'U' = Unknown ---
if 'Cabin' in df.columns:
    # 77% хоосон: устгахын оронд эхний үсэг (A,B,C...) = давхрыг шинж болгох
    df['Deck'] = df['Cabin'].fillna('U').str[0]
    df.drop('Cabin', axis=1, inplace=True)
    print("Cabin -> Deck шинж үүсгэлээ (U = Unknown):")
    print(df['Deck'].value_counts())

# --- 5) Шаардлагагүй багануудыг устгах (Title-ийн ДАРАА!) ---
columns_to_drop = ['Name', 'Ticket']
existing_columns = [col for col in columns_to_drop if col in df.columns]
if existing_columns:
    df.drop(existing_columns, axis=1, inplace=True)
    print(f"{existing_columns} багануудыг устгав")

# Дүүргэлтийн ДАРААХ хоосон утгын тайлан (нотолгоо)
print("\nДүүргэлтийн дараах хоосон утга:")
missing_after = df.isnull().sum()
if missing_after.sum() == 0:
    print("   Хоосон утга үлдээгүй")
else:
    print(missing_after[missing_after > 0])

print("Цэвэрлэгээний дараах өгөгдлийн хэмжээ:", df.shape)
print("Шинээр үүссэн шинжүүд:",
      [c for c in ['Title', 'Deck', 'Age_was_missing'] if c in df.columns])

# АЛХАМ 4: Амьд үлдэх ерөнхий статистик
print("\nАЛХАМ 4: Амьд үлдэх ерөнхий статистик")
print("-" * 30)

if 'Survived' in df.columns:
    survival_rate = df['Survived'].mean()
    print(f"Ерөнхий амьд үлдэх хувь: {survival_rate:.1%}")
    print(f"Нийт хүн: {len(df)}")
    print(f"Амьд үлдсэн: {df['Survived'].sum()}")
    print(f"Нас барсан: {len(df) - df['Survived'].sum()}")
else:
    print("'Survived' багана олдсонгүй")

# АЛХАМ 5: Ангиар шинжилгээ
print("\nАЛХАМ 5: Ангиар шинжилгээ")
print("-" * 30)

if 'Pclass' in df.columns and 'Survived' in df.columns:
    class_survival = df.groupby('Pclass')['Survived'].agg(['count', 'sum', 'mean'])
    class_survival.columns = ['Нийт', 'Амьд үлдсэн', 'Хувь']
    class_survival['Хувь'] = class_survival['Хувь'] * 100
    print("Ангиар ангилсан амьд үлдэх харьцаа:")
    print(class_survival.round(1))
    
    # График зурах
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    class_survival['Хувь'].plot(kind='bar', color=['gold', 'silver', 'brown'])
    plt.title('Ангиар амьд үлдэх хувь')
    plt.xlabel('Анги')
    plt.ylabel('Хувь (%)')
    plt.xticks(rotation=0)

# АЛХАМ 6: Хүйсээр шинжилгээ
print("\nАЛХАМ 6: Хүйсээр шинжилгээ")
print("-" * 30)

if 'Sex' in df.columns and 'Survived' in df.columns:
    gender_survival = df.groupby('Sex')['Survived'].agg(['count', 'sum', 'mean'])
    gender_survival.columns = ['Нийт', 'Амьд үлдсэн', 'Хувь']
    gender_survival['Хувь'] = gender_survival['Хувь'] * 100
    gender_survival.index = ['Эмэгтэй', 'Эрэгтэй']
    print("Хүйсээр ангилсан амьд үлдэх харьцаа:")
    print(gender_survival.round(1))
    
    # График зурах
    plt.subplot(1, 2, 2)
    gender_survival['Хувь'].plot(kind='bar', color=['pink', 'lightblue'])
    plt.title('Хүйсээр амьд үлдэх хувь')
    plt.xlabel('Хүйс')
    plt.ylabel('Хувь (%)')
    plt.xticks(rotation=0)
    
    plt.tight_layout()
    plt.show()

# АЛХАМ 7: Насны шинжилгээ
print("\nАЛХАМ 7: Насны шинжилгээ")
print("-" * 30)

if 'Age' in df.columns and 'Survived' in df.columns:
    # Насны бүлэг үүсгэх
    df['AgeGroup'] = pd.cut(df['Age'], 
                           bins=[0, 10, 20, 30, 40, 50, 60, 100],
                           labels=['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '60+'])
    
    age_survival = df.groupby('AgeGroup')['Survived'].agg(['count', 'mean'])
    age_survival.columns = ['Тоо', 'Амьд үлдэх хувь']
    age_survival['Амьд үлдэх хувь'] = age_survival['Амьд үлдэх хувь'] * 100
    print("Насны бүлгээр амьд үлдэх харьцаа:")
    print(age_survival.round(1))
    
    # График
    plt.figure(figsize=(10, 5))
    age_survival['Амьд үлдэх хувь'].plot(kind='bar', color='skyblue')
    plt.title('Насны бүлгээр амьд үлдэх хувь')
    plt.xlabel('Насны бүлэг')
    plt.ylabel('Хувь (%)')
    plt.xticks(rotation=45)
    plt.show()

# АЛХАМ 8: Тийм сүүлийн үнийн шинжилгээ
print("\nАЛХАМ 8: Тийм сүүлийн үнийн шинжилгээ")
print("-" * 30)

if 'Fare' in df.columns and 'Survived' in df.columns:
    # Үнийн бүлэг үүсгэх
    df['FareGroup'] = pd.cut(df['Fare'], 
                            bins=[0, 10, 50, 100, df['Fare'].max() + 1],
                            labels=['0-10', '10-50', '50-100', '100+'])
    
    fare_survival = df.groupby('FareGroup')['Survived'].agg(['count', 'mean'])
    fare_survival.columns = ['Тоо', 'Амьд үлдэх хувь']
    fare_survival['Амьд үлдэх хувь'] = fare_survival['Амьд үлдэх хувь'] * 100
    print("Тийм сүүлийн үнээр амьд үлдэх харьцаа:")
    print(fare_survival.round(1))

# АЛХАМ 9: Корреляцийн шинжилгээ
print("\nАЛХАМ 9: Корреляцийн шинжилгээ")
print("-" * 30)

# Тоон хувьсагчдын корреляци
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 1:
    correlation_matrix = df[numeric_cols].corr()
    print("Корреляцийн матриц:")
    print(correlation_matrix.round(3))
    
    if 'Survived' in correlation_matrix.columns:
        print(f"\nАмьд үлдэхтэй хамгийн их хамааралтай:")
        survived_corr = correlation_matrix['Survived'].abs().sort_values(ascending=False)
        for col, corr in survived_corr.items():
            if col != 'Survived':
                print(f"   {col}: {corr:.3f}")

# АЛХАМ 10: Машин сургалтын энгийн загвар
print("\nАЛХАМ 10: Машин сургалтын загвар")
print("-" * 30)

try:
    # Категорын өгөгдлийг тоо болгон хувиргах
    df_model = df.copy()
    
    # Sex багананы кодлол
    if 'Sex' in df_model.columns:
        df_model['Sex'] = df_model['Sex'].map({'male': 1, 'female': 0})
    
    # Embarked багананы кодлол
    if 'Embarked' in df_model.columns:
        df_model = pd.get_dummies(df_model, columns=['Embarked'], prefix='Embarked')

    # Шинээр үүссэн категор багануудыг (Title, Deck) тоо болгон хувиргах
    # get_dummies-ийн дараа анхдагч Title/Deck үлдэхгүй -> шинэ кодлогдсон баганууд нь шинж болно
    cat_cols = [c for c in ['Title', 'Deck'] if c in df_model.columns]
    if cat_cols:
        df_model = pd.get_dummies(df_model, columns=cat_cols,
                                  prefix=cat_cols)
        print(f"{cat_cols} багануудыг one-hot кодлол хийв")
    
    # Шаардлагатай багануудыг сонгох
    feature_cols = [col for col in df_model.columns if col not in ['Survived', 'PassengerId', 'AgeGroup', 'FareGroup']]
    
    if 'Survived' in df_model.columns and len(feature_cols) > 0:
        X = df_model[feature_cols]
        y = df_model['Survived']
        
        # Хоосон утгыг арилгах
        X = X.fillna(0)
        
        # Сургалт болон тест өгөгдөлд хуваах
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Random Forest загвар
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Таамаглал хийх
        y_pred = model.predict(X_test)
        
        # Үр дүн
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Загварын нарийвчлал: {accuracy:.1%}")
        
        # Хувьсагчдын ач холбогдол
        feature_importance = pd.DataFrame({
            'Хувьсагч': feature_cols,
            'Ач холбогдол': model.feature_importances_
        }).sort_values('Ач холбогдол', ascending=False)
        
        print("\nХувьсагчдын ач холбогдол:")
        for i, row in feature_importance.head().iterrows():
            print(f"   {row['Хувьсагч']}: {row['Ач холбогдол']:.3f}")
    
except Exception as e:
    print(f"Машин сургалтын загварт алдаа: {e}")

# ЭЦСИЙН ДҮГНЭЛТ
print("\n" + "="*60)
print("ЭЦСИЙН ДҮГНЭЛТ")
print("="*60)

if 'Survived' in df.columns:
    print(f"""
ТИТАНИК ӨГӨГДЛИЙН ШИНЖИЛГЭЭНИЙ ҮР ДҮҮН:

Ерөнхий үзүүлэлт:
   • Нийт зорчигч: {len(df)} хүн
   • Амьд үлдэх хувь: {df['Survived'].mean():.1%}

Гол дүгнэлтүүд:
   • Хүйс хамгийн чухал хүчин зүйл
   • Нийгмийн анги чухал нөлөө үзүүлсэн
   • Эдийн засгийн байдал амьд үлдэхтэй холбоотой
   • "Эмэгтэй, хүүхэд эхлээд" зарчим бодитой

Сургамж:
   • Өгөгдөл цэвэрлэгээ чухал
   • Олон өнцгөөс шинжлэх хэрэгтэй
   • Дүрслэл ойлголтод тусалдаг
   • Статистик болон машин сургалт хослуулах нь үр дүнтэй
    """)

print("\nШинжилгээ дуусгавар болов!")
print("Дараагийн алхам: Илүү нарийвчилсан загвар бүтээх, cross-validation хийх")

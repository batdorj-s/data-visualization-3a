import React, { useState, useEffect } from 'react';


const TitanicAnalysisTutorial = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Симуляци өгөгдөл (Титаникийн жинхэнэ өгөгдөл дээр тулгуурласан)
  const rawData = [
    { PassengerId: 1, Survived: 0, Pclass: 3, Name: "Braund, Mr. Owen Harris", Sex: "male", Age: 22, SibSp: 1, Parch: 0, Fare: 7.25, Embarked: "S" },
    { PassengerId: 2, Survived: 1, Pclass: 1, Name: "Cumings, Mrs. John Bradley", Sex: "female", Age: 38, SibSp: 1, Parch: 0, Fare: 71.28, Embarked: "C" },
    { PassengerId: 3, Survived: 1, Pclass: 3, Name: "Heikkinen, Miss. Laina", Sex: "female", Age: 26, SibSp: 0, Parch: 0, Fare: 7.92, Embarked: "S" },
    { PassengerId: 4, Survived: 1, Pclass: 1, Name: "Futrelle, Mrs. Jacques Heath", Sex: "female", Age: 35, SibSp: 1, Parch: 0, Fare: 53.10, Embarked: "S" },
    { PassengerId: 5, Survived: 0, Pclass: 3, Name: "Allen, Mr. William Henry", Sex: "male", Age: 35, SibSp: 0, Parch: 0, Fare: 8.05, Embarked: "S" }
  ];

  // Шинжилгээний үр дүнгийн өгөгдөл
  const survivalByClass = [
    { class: "1-р анги", survived: 136, died: 80, total: 216, rate: 63 },
    { class: "2-р анги", survived: 87, died: 97, total: 184, rate: 47 },
    { class: "3-р анги", survived: 119, died: 372, total: 491, rate: 24 }
  ];

  const survivalByGender = [
    { gender: "Эмэгтэй", survived: 233, died: 81, rate: 74.2 },
    { gender: "Эрэгтэй", survived: 109, died: 468, rate: 18.9 }
  ];

  const ageDistribution = [
    { ageGroup: "0-10", count: 62 },
    { ageGroup: "11-20", count: 102 },
    { ageGroup: "21-30", count: 220 },
    { ageGroup: "31-40", count: 167 },
    { ageGroup: "41-50", count: 89 },
    { ageGroup: "51-60", count: 42 },
    { ageGroup: "60+", count: 32 }
  ];

  const fareAnalysis = [
    { range: "0-10", count: 515, avgSurvival: 0.197 },
    { range: "10-50", count: 302, avgSurvival: 0.424 },
    { range: "50-100", count: 60, avgSurvival: 0.667 },
    { range: "100+", count: 14, avgSurvival: 0.786 }
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  const steps = [
    {
      title: "1. Асуудал тодорхойлох",
      content: "Титаникийн сүйрлийн үеэр амьд үлдэх магадлалд юу нөлөөлсөн бэ?",
      code: `# Асуудал тодорхойлох
# - Юу шинжлэх вэ: Амьд үлдэх магадлал
# - Хувьсагчид: Анги, хүйс, нас, тийм сүүл
# - Зорилго: Амьд үлдэхэд нөлөөлөх хүчин зүйлс олох`,
      visual: null
    },
    {
      title: "2. Өгөгдөл ачаалах болон анхдагч судалгаа",
      content: "Өгөгдлийн бүтэц, хэмжээ, төрлийг ойлгох",
      code: `import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Өгөгдөл ачаалах
df = pd.read_csv('titanic.csv')

# Үндсэн мэдээлэл
print(f"Өгөгдлийн хэмжээ: {df.shape}")
print(f"Багануудын тоо: {df.columns.tolist()}")
print(f"Хоосон утгууд:\\n{df.isnull().sum()}")`,
      visual: "info"
    },
    {
      title: "3. Өгөгдлийн цэвэрлэгээ",
      content: "Хоосон утга, алдаа засах",
      code: `# Насны хоосон утгыг дундаж утгаар орлуулах
df['Age'].fillna(df['Age'].median(), inplace=True)

# Суугалт газрын хоосон утгыг модаар орлуулах  
df['Embarked'].fillna(df['Embarked'].mode()[0], inplace=True)

# Шаардлагагүй багануудыг устгах
df.drop(['Name', 'Ticket', 'Cabin'], axis=1, inplace=True)`,
      visual: null
    },
    {
      title: "4. Танин мэдэх шинжилгээ (EDA)",
      content: "Өгөгдлийн тархалт, хамаарлыг судлах",
      code: `# Амьд үлдэх ерөнхий статистик
survival_rate = df['Survived'].mean()
print(f"Ерөнхий амьд үлдэх хувь: {survival_rate:.1%}")

# Ангиар ангилсан амьд үлдэх хувь
class_survival = df.groupby('Pclass')['Survived'].agg(['count', 'sum', 'mean'])
print(class_survival)`,
      visual: "survival_by_class"
    },
    {
      title: "5. Хүйсээр шинжлэх",
      content: "Эрэгтэй, эмэгтэй хүмүүсийн амьд үлдэх харьцаа",
      code: `# Хүйсээр ангилсан шинжилгээ
gender_survival = df.groupby('Sex')['Survived'].agg(['count', 'sum', 'mean'])
print("Хүйсээр амьд үлдэх харьцаа:")
print(gender_survival)

# Хүйс болон ангийн хосолсон нөлөө
pivot_table = df.pivot_table('Survived', index='Sex', columns='Pclass', aggfunc='mean')
print(pivot_table)`,
      visual: "survival_by_gender"
    },
    {
      title: "6. Насны шинжилгээ",
      content: "Насны бүлгээр амьд үлдэх магадлал",
      code: `# Насны тархалт
df['AgeGroup'] = pd.cut(df['Age'], 
                       bins=[0, 10, 20, 30, 40, 50, 60, 100],
                       labels=['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '60+'])

age_survival = df.groupby('AgeGroup')['Survived'].agg(['count', 'mean'])
print("Насны бүлгээр амьд үлдэх харьцаа:")
print(age_survival)`,
      visual: "age_distribution"
    },
    {
      title: "7. Тийм сүүлийн үнийн шинжилгээ",
      content: "Тийм сүүлийн үнэ ба амьд үлдэх хоорондын хамаарал",
      code: `# Тийм сүүлийн үнийн бүлэглэл
df['FareGroup'] = pd.cut(df['Fare'], 
                        bins=[0, 10, 50, 100, 1000],
                        labels=['0-10', '10-50', '50-100', '100+'])

fare_survival = df.groupby('FareGroup')['Survived'].agg(['count', 'mean'])
print("Тийм сүүлийн үнээр амьд үлдэх харьцаа:")
print(fare_survival)`,
      visual: "fare_analysis"
    },
    {
      title: "8. Корреляцийн шинжилгээ",
      content: "Хувьсагчид хоорондын хамаарлыг судлах",
      code: `# Тоон хувьсагчдын хамаарал
correlation_matrix = df[['Survived', 'Pclass', 'Age', 'SibSp', 'Parch', 'Fare']].corr()
print("Корреляцийн матриц:")
print(correlation_matrix['Survived'].sort_values(ascending=False))

# Гол дүгнэлт:
# - Анги (-0.34): Доод анги = бага амьд үлдэх магадлал
# - Тийм сүүлийн үнэ (0.26): Өндөр үнэ = өндөр амьд үлдэх магадлал`,
      visual: "correlation"
    },
    {
      title: "9. Дүгнэлт болон зөвлөмж",
      content: "Шинжилгээний үр дүнг нэгтгэх",
      code: `# Гол дүгнэлтүүд:
print("""
ТИТАНИК ӨГӨГДЛИЙН ШИНЖИЛГЭЭНИЙ ҮР ДҮҮН:

1. Ерөнхий амьд үлдэх хувь: 38.4%

2. Хүйсийн нөлөө:
   - Эмэгтэй: 74.2% амьд үлдсэн
   - Эрэгтэй: 18.9% амьд үлдсэн

3. Ангийн нөлөө:
   - 1-р анги: 63% амьд үлдсэн  
   - 2-р анги: 47% амьд үлдсэн
   - 3-р анги: 24% амьд үлдсэн

4. Тийм сүүлийн үнийн нөлөө:
   - Өндөр үнэтэй тасалбар = өндөр амьд үлдэх магадлал

5. "Эмэгтэй, хүүхэд эхлээд" зарчим бодитоор хэрэгжсэн
""")`,
      visual: "conclusion"
    }
  ];

  const renderVisualization = () => {
    const currentStepData = steps[currentStep - 1];
    
    switch(currentStepData.visual) {
      case 'info':
        return (
          <div className="bg-slate-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Өгөгдлийн ерөнхий мэдээлэл</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Мөр:</strong> 891<br/>
                <strong>Багана:</strong> 12<br/>
                <strong>Хувьсагчид:</strong> PassengerId, Survived, Pclass, Name, Sex, Age, SibSp, Parch, Fare, Embarked
              </div>
              <div>
                <strong>Хоосон утгууд:</strong><br/>
                Age: 177<br/>
                Embarked: 2<br/>
                Cabin: 687
              </div>
            </div>
          </div>
        );

      case 'survival_by_class':
        return (
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Ангиар ангилсан амьд үлдэх харьцаа</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={survivalByClass}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="class" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="survived" fill="#00C49F" name="Амьд үлдсэн" />
                <Bar dataKey="died" fill="#FF8042" name="Нас барсан" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'survival_by_gender':
        return (
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Хүйсээр ангилсан амьд үлдэх харьцаа</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={survivalByGender}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="rate"
                  label={({gender, rate}) => `${gender}: ${rate}%`}
                >
                  {survivalByGender.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      case 'age_distribution':
        return (
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Насны бүлгийн тархалт</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ageDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ageGroup" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#0088FE" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'fare_analysis':
        return (
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Тийм сүүлийн үнэ ба амьд үлдэх харьцаа</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={fareAnalysis}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Амьд үлдэх хувь']} />
                <Line type="monotone" dataKey="avgSurvival" stroke="#00C49F" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'correlation':
        return (
          <div className="bg-slate-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-3">Корреляцийн дүн</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Pclass (Анги):</span>
                <span className="font-mono text-red-600">-0.338</span>
              </div>
              <div className="flex justify-between">
                <span>Fare (Тийм сүүл):</span>
                <span className="font-mono text-green-600">+0.257</span>
              </div>
              <div className="flex justify-between">
                <span>Age (Нас):</span>
                <span className="font-mono text-red-400">-0.077</span>
              </div>
              <div className="flex justify-between">
                <span>SibSp (Ах дүү эхнэр):</span>
                <span className="font-mono text-red-400">-0.035</span>
              </div>
            </div>
          </div>
        );

      case 'conclusion':
        return (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
            <h4 className="font-bold text-lg mb-4">Эцсийн дүгнэлт</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="bg-white p-3 rounded">
                  <div className="font-semibold text-green-700">Амьд үлдэхэд тусалсан хүчин зүйлүүд:</div>
                  <ul className="text-sm mt-2 space-y-1">
                    <li>• Эмэгтэй хүйс</li>
                    <li>• Дээд анги (1, 2-р анги)</li>
                    <li>• Өндөр үнэтэй тасалбар</li>
                  </ul>
                </div>
              </div>
              <div className="space-y-3">
                <div className="bg-white p-3 rounded">
                  <div className="font-semibold text-red-700">Эрсдэлтэй хүчин зүйлүүд:</div>
                  <ul className="text-sm mt-2 space-y-1">
                    <li>• Эрэгтэй хүйс</li>
                    <li>• 3-р анги</li>
                    <li>• Хямд тасалбар</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const simulateAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
    }, 2000);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Титаник өгөгдлийн шинжилгээ - Практик жишээ
        </h1>
        <p className="text-lg text-gray-600">
          Алхам алхамаар өгөгдлийн шинжилгээ хийх арга зүйг Титаникийн өгөгдөл дээр сурцгаая
        </p>
      </div>

      {/* Алхамын навигаци */}
      <div className="mb-8">
        <div className="flex flex-wrap gap-2">
          {steps.map((step, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index + 1)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentStep === index + 1
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {index + 1}. {step.title.split('.')[1]?.trim() || step.title}
            </button>
          ))}
        </div>
      </div>

      {/* Тухайн алхамын агуулга */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Код болон тайлбар */}
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold mb-3">{steps[currentStep - 1].title}</h2>
            <p className="text-gray-600 mb-4">{steps[currentStep - 1].content}</p>
          </div>

          {steps[currentStep - 1].code && (
            <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-medium">Python код</span>
                <button
                  onClick={simulateAnalysis}
                  className="flex items-center gap-2 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Ажиллаж байна...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Ажиллуулах
                    </>
                  )}
                </button>
              </div>
              <pre className="text-sm overflow-x-auto">
                <code>{steps[currentStep - 1].code}</code>
              </pre>
            </div>
          )}

          {/* Өгөгдлийн жишээ хүснэгт */}
          {currentStep === 2 && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-3">Өгөгдлийн жишээ (эхний 5 мөр)</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="bg-gray-200">
                      <th className="p-2 text-left">ID</th>
                      <th className="p-2 text-left">Амьд үлдсэн</th>
                      <th className="p-2 text-left">Анги</th>
                      <th className="p-2 text-left">Хүйс</th>
                      <th className="p-2 text-left">Нас</th>
                      <th className="p-2 text-left">Тийм сүүл</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rawData.map((row, i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="p-2">{row.PassengerId}</td>
                        <td className="p-2">{row.Survived ? 'Тийм' : 'Үгүй'}</td>
                        <td className="p-2">{row.Pclass}-р анги</td>
                        <td className="p-2">{row.Sex === 'male' ? 'Эрэгтэй' : 'Эмэгтэй'}</td>
                        <td className="p-2">{row.Age}</td>
                        <td className="p-2">${row.Fare}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Дүрслэл */}
        <div className="space-y-6">
          {renderVisualization()}
          
          {/* Алхамын үр дүн */}
          {currentStep === 4 && (
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-2">Анхны олдвор</h4>
              <ul className="text-sm text-green-700 space-y-1">
                <li>• Ерөнхий амьд үлдэх хувь: 38.4%</li>
                <li>• 1-р анги: 63% амьд үлдсэн</li>
                <li>• 2-р анги: 47% амьд үлдсэн</li>
                <li>• 3-р анги: 24% амьд үлдсэн</li>
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Навигацийн товчлууруд */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className="px-6 py-2 bg-gray-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
        >
          ← Өмнөх алхам
        </button>
        
        <span className="flex items-center text-gray-600">
          Алхам {currentStep} / {steps.length}
        </span>
        
        <button
          onClick={() => setCurrentStep(Math.min(steps.length, currentStep + 1))}
          disabled={currentStep === steps.length}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
        >
          Дараах алхам →
        </button>
      </div>

      {/* Нэмэлт ресурс */}
      <div className="mt-8 p-6 bg-blue-50 rounded-lg">
        <h3 className="font-bold text-blue-900 mb-3">Нэмэлт ресурсууд</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <strong>Өгөгдлийн эх үүсвэр:</strong><br/>
            <a href="https://www.kaggle.com/c/titanic" className="text-blue-600 underline">Kaggle Titanic Competition</a>
          </div>
          <div>
            <strong>Ашигласан сангууд:</strong><br/>
            pandas, numpy, matplotlib, seaborn
          </div>
          <div>
            <strong>Дараагийн алхам:</strong><br/>
            Машин сургалтын загвар бүтээх
          </div>
        </div>
      </div>
    </div>
  );
};

export default TitanicAnalysisTutorial;
import json

with open('models/training_results.json') as f:
    results = json.load(f)

print('=' * 55)
print('   FPS PREDICTION MODEL RESULTS')
print('=' * 55)

for model, metrics in results.items():
    print(f'\n  {model}')
    print(f'    R2 Score  : {metrics["R2"]} ({metrics["R2"]*100:.1f}% variance explained)')
    print(f'    MAE       : {metrics["MAE"]} FPS')
    print(f'    RMSE      : {metrics["RMSE"]} FPS')
    print(f'    Accuracy  : {metrics["accuracy_pct"]}%')

print()

with open('models/model_meta.json') as f:
    meta = json.load(f)

print(f'  Best Model : {meta["best_model"]}')
print(f'  Trained At : {meta["trained_at"]}')
print('=' * 55)
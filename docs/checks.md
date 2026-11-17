# Перевірки Wishlist API

## Обов’язкові перевірки

Для `main` діє ruleset із обов’язковим pull request, актуальністю щодо `main`, скиданням застарілих схвалень і забороною видалення та force-push. Список обходу порожній. В індивідуальній роботі кількість обов’язкових схвалень дорівнює нулю. Для злиття мають пройти `API lint`, `API tests (Python 3.12)` і `API tests (Python 3.13)`. [Налаштування ruleset](https://github.com/w1xes/wishlist-api/rules/27492370)

1. На коміті `765e9ba` GitHub повернув `mergeStateStatus: BLOCKED` для PR №1, а тести на обох версіях Python завершилися помилкою. [PR №1](https://github.com/w1xes/wishlist-api/pull/1) · [Невдалий прогін](https://github.com/w1xes/wishlist-api/actions/runs/44167112400)
2. У тесті `test_health_without_database` журнал показав `AssertionError: assert {'status': 'ok'} == {'status': 'broken'}`. Звіти `api-coverage-py3.12` та `api-coverage-py3.13` залишилися серед артефактів прогону. [Журнал pytest](https://github.com/w1xes/wishlist-api/actions/runs/44167112400/job/134336097205)
3. У тому самому PR коміт `2eb4b96` повернув правильне очікування `ok` і додав тест на порожню назву бажання. Лінтер і обидва завдання матриці пройшли, а GitHub повернув `mergeStateStatus: CLEAN`. [Виправлення](https://github.com/w1xes/wishlist-api/pull/1/commits/2eb4b96623b61237a6784bedff8715a1ad2935e2) · [Успішний прогін](https://github.com/w1xes/wishlist-api/actions/runs/44167373652)

Стан злиття перевірено через GitHub CLI. Знімки екрана для завдання 4 ще потрібно додати.

## Вимірювання кешу

Дві спроби того самого прогону на `main`, коміт `7aa43a2`. Час узято з міток початку й завершення спроб у GitHub Actions.

| Прогін | Час |
|---|---:|
| [Без кешу](https://github.com/w1xes/wishlist-api/actions/runs/44166854130/attempts/1) | 59 с |
| [З кешем](https://github.com/w1xes/wishlist-api/actions/runs/44166854130/attempts/2) | 61 с |

Найдовший крок — `Initialize containers`, 14 с у першій спробі.

У другій спробі обидва завдання матриці відновили кеш, пропустили завантаження wheels і встановили залежності локально з `.wheelhouse`. Повний прогін тривав на 2 с довше.

## Нічний аудит

Окремий workflow `API dependency audit` запускає `pip-audit`. Ручний контрольний запуск завершився без знахідок. [Результат аудиту](https://github.com/w1xes/wishlist-api/actions/runs/44167176255)

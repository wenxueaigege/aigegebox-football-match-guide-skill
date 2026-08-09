#!/usr/bin/env python3
"""Build the as-of-2026-08-08 Real Madrid guide sample from reviewed sources."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "examples" / "real-madrid-2026-27-2026-08-08.json"
UPDATED = "2026-08-08"
RM_SOURCE = "https://www.realmadrid.com/en-US/"
LALIGA_SOURCE = "https://www.realmadrid.com/en-US/news/football/first-team/latest-news/el-calendario-del-real-madrid-para-la-liga-2026-27-30-06-2026"
UEFA_SOURCE = "https://www.uefa.com/uefachampionsleague/news/02a6-20e5a8be4e63-ae971c582f8c-1000--champions-league-qualifying-fixtures-dates-how-it-works/"


def fixture(
    fixture_id: str,
    competition: str,
    competition_type: str,
    stage: str,
    date: str | None,
    opponent: str | None,
    venue: str | None,
    location: str | None,
    *,
    time: str | None = None,
    status: str = "tbd",
    source: str = RM_SOURCE,
    date_label: str | None = None,
    broadcasts: list[dict] | None = None,
    note: str = "",
) -> dict:
    item = {
        "fixtureId": fixture_id,
        "competition": competition,
        "competitionType": competition_type,
        "stage": stage,
        "date": date,
        "time": time,
        "opponent": opponent,
        "venue": venue,
        "location": location,
        "status": status,
        "broadcasts": broadcasts or [],
        "source": source,
        "updatedAt": UPDATED,
        "note": note,
    }
    if date_label:
        item["dateLabel"] = date_label
    return item


def main() -> None:
    fixtures: list[dict] = [
        fixture("rm-friendly-20260801-fiorentina", "Official Friendlies", "friendly", "季前赛", "2026-08-02", "佛罗伦萨", "neutral", "Wörthersee Stadion（克拉根福）", time="00:00", status="finished", note="奥地利当地8月1日18:00；北京时间8月2日00:00。"),
        fixture("rm-friendly-20260809-ferencvaros", "Official Friendlies", "friendly", "季前赛", "2026-08-09", "费伦茨瓦罗斯", "away", "Groupama Arena（布达佩斯）", time="01:00", status="scheduled", source="https://www.realmadrid.com/en-US/news/football/first-team/latest-news/el-real-madrid-disputara-contra-el-ferencvaros-un-amistoso-en-hungria-el-8-de-agosto-24-07-2026", note="匈牙利当地8月8日19:00；北京时间8月9日01:00。中国大陆转播待定。"),
        fixture("rm-friendly-20260813-deportivo", "Official Friendlies", "friendly", "特雷莎·埃雷拉杯", "2026-08-13", "拉科鲁尼亚", "away", "Estadio Abanca-Riazor（拉科鲁尼亚）", time="03:00", status="scheduled", source="https://www.realmadrid.com/en-US/football/games/soccer-champions-tour/deportivo-de-a-coruna-real-madrid/12-08-2026", note="西班牙当地8月12日21:00；北京时间8月13日03:00。中国大陆转播待定。"),
        fixture("rm-friendly-20260816-schalke", "Official Friendlies", "friendly", "季前赛", "2026-08-16", "沙尔克04", "away", "VELTINS-Arena（盖尔森基兴）", time="23:00", status="scheduled", source="https://www.realmadrid.com/en-US/news/football/first-team/latest-news/el-real-madrid-disputara-un-amistoso-contra-el-schalke-04-el-16-de-agosto-29-07-2026", note="德国当地8月16日17:00；北京时间8月16日23:00。中国大陆转播待定。"),
    ]

    league = [
        ("01", "2026-08-23", "8月22-23日", "西班牙人", "away", "RCDE Stadium", "03:30", "第1轮"),
        ("02", "2026-08-27", "8月26日", "皇家社会", "home", "Santiago Bernabéu", "03:00", "第2轮"),
        ("03", "2026-08-30", "8月29-30日", "马拉加", "home", "Santiago Bernabéu", "23:00", "第3轮"),
        ("04", "2026-09-06", "9月5-6日", "皇家贝蒂斯", "away", "Estadio La Cartuja de Sevilla", None, "第4轮"),
        ("05", "2026-09-12", "9月12-13日", "巴列卡诺", "home", "Santiago Bernabéu", None, "第5轮"),
        ("06", "2026-09-15", "9月15-16日", "埃尔切", "away", "Estadio Manuel Martínez Valero", None, "第6轮"),
        ("07", "2026-09-19", "9月19-20日", "马德里竞技", "away", "Metropolitano", None, "第7轮"),
        ("08", "2026-10-10", "10月10-11日", "比利亚雷亚尔", "home", "Santiago Bernabéu", None, "第8轮"),
        ("09", "2026-10-17", "10月17-18日", "塞维利亚", "home", "Santiago Bernabéu", None, "第9轮"),
        ("10", "2026-10-24", "10月24-25日", "巴塞罗那", "away", "Spotify Camp Nou", None, "第10轮"),
        ("11", "2026-10-31", "10月31日-11月1日", "桑坦德竞技", "away", "Campos de Sport de El Sardinero", None, "第11轮"),
        ("12", "2026-11-07", "11月7-8日", "瓦伦西亚", "away", "Mestalla", None, "第12轮"),
        ("13", "2026-11-21", "11月21-22日", "塞尔塔", "home", "Santiago Bernabéu", None, "第13轮"),
        ("14", "2026-11-28", "11月28-29日", "阿拉维斯", "home", "Santiago Bernabéu", None, "第14轮"),
        ("15", "2026-12-05", "12月5-6日", "毕尔巴鄂竞技", "away", "San Mamés", None, "第15轮"),
        ("16", "2026-12-12", "12月12-13日", "奥萨苏纳", "home", "Santiago Bernabéu", None, "第16轮"),
        ("17", "2026-12-19", "12月19-20日", "拉科鲁尼亚", "home", "Santiago Bernabéu", None, "第17轮"),
        ("18", "2027-01-02", "1月2-3日", "赫塔费", "home", "Santiago Bernabéu", None, "第18轮"),
        ("19", "2027-01-09", "1月9-10日", "莱万特", "home", "Santiago Bernabéu", None, "第19轮"),
        ("20", "2027-01-16", "1月16-17日", "马拉加", "away", "La Rosaleda", None, "第20轮"),
        ("21", "2027-01-23", "1月23-24日", "皇家贝蒂斯", "home", "Santiago Bernabéu", None, "第21轮"),
        ("22", "2027-01-30", "1月30-31日", "巴列卡诺", "away", "Estadio de Vallecas", None, "第22轮"),
        ("23", "2027-02-06", "2月6-7日", "皇家社会", "away", "Reale Arena", None, "第23轮"),
        ("24", "2027-02-13", "2月13-14日", "毕尔巴鄂竞技", "home", "Santiago Bernabéu", None, "第24轮"),
        ("25", "2027-02-20", "2月20-21日", "塞维利亚", "away", "Ramón Sánchez-Pizjuán", None, "第25轮"),
        ("26", "2027-02-27", "2月27-28日", "瓦伦西亚", "home", "Santiago Bernabéu", None, "第26轮"),
        ("27", "2027-03-06", "3月6-7日", "比利亚雷亚尔", "away", "Estadio de la Cerámica", None, "第27轮"),
        ("28", "2027-03-13", "3月13-14日", "西班牙人", "home", "Santiago Bernabéu", None, "第28轮"),
        ("29", "2027-03-20", "3月20-21日", "塞尔塔", "away", "Abanca-Balaídos", None, "第29轮"),
        ("30", "2027-04-03", "4月3-4日", "马德里竞技", "home", "Santiago Bernabéu", None, "第30轮"),
        ("31", "2027-04-10", "4月10-11日", "奥萨苏纳", "away", "El Sadar", None, "第31轮"),
        ("32", "2027-04-17", "4月17-18日", "赫塔费", "away", "Coliseum", None, "第32轮"),
        ("33", "2027-04-20", "4月20-21日", "埃尔切", "home", "Santiago Bernabéu", None, "第33轮"),
        ("34", "2027-05-01", "5月1-2日", "莱万特", "away", "Ciutat de València", None, "第34轮"),
        ("35", "2027-05-08", "5月8-9日", "巴塞罗那", "home", "Santiago Bernabéu", None, "第35轮"),
        ("36", "2027-05-15", "5月15-16日", "桑坦德竞技", "home", "Santiago Bernabéu", None, "第36轮"),
        ("37", "2027-05-22", "5月22-23日", "阿拉维斯", "away", "Mendizorroza", None, "第37轮"),
        ("38", "2027-05-29", "5月29-30日", "拉科鲁尼亚", "home", "Santiago Bernabéu", None, "第38轮"),
    ]
    for round_no, match_date, date_label, opponent, venue, location, time, stage in league:
        fixtures.append(fixture(
            f"rm-laliga-{round_no}", "La Liga", "domestic-league", stage, match_date, opponent, venue, location,
            time=time, status="confirmed" if time else "scheduled", source=LALIGA_SOURCE, date_label=date_label,
            note="官方公布比赛周末窗口；具体开球时间待官方确认。" if not time else "北京时间；时间来自皇家马德里官方当前赛程页。",
        ))

    fixtures.extend([
        fixture("rm-copa-del-rey-tbd", "Copa del Rey", "domestic-cup", "赛程待抽签", None, "对手待定", None, "场地待定", source="https://rfef.es/es/competiciones/copa-del-rey", note="国王杯对阵、轮次和日期待官方抽签及赛历确认。"),
        fixture("rm-supercopa-tbd", "Supercopa de España", "super-cup", "赛程待定", None, "对手待定", "neutral", "场地待定", source="https://rfef.es/es/competiciones/supercopa-de-espana", note="西班牙超级杯参赛对阵和日期待官方确认。"),
        fixture("rm-ucl-tbd", "UEFA Champions League", "continental", "联赛阶段待抽签", None, "对手待定", None, "场地待定", source=UEFA_SOURCE, note="欧冠联赛阶段抽签安排在2026年8月27日；对手、比赛日和场地待定。"),
    ])

    payload = {
        "team": {"teamId": "real-madrid", "nameZh": "皇家马德里", "nameEn": "Real Madrid"},
        "season": "2026/27",
        "region": "CN-mainland",
        "lastCheckedAt": UPDATED,
        "asOfDate": UPDATED,
        "sourceMode": "official-current-snapshot",
        "sourceTimeZone": "Europe/Madrid",
        "displayTimeZone": "Asia/Shanghai",
        "dataNote": "皇家马德里男子一线队 2026/27 赛季真实测试快照。友谊赛和西甲前三场使用皇家马德里官方当前赛程信息；西甲其余比赛使用俱乐部公布的轮次窗口。中国大陆逐场转播没有可靠官方确认时统一显示“转播待定”。欧冠、国王杯和西超杯尚未完成抽签或官方排期，保留待定入口，不把推测写成比赛事实。",
        "expectedCompetitions": ["La Liga", "Copa del Rey", "Supercopa de España", "UEFA Champions League", "Official Friendlies"],
        "sources": [
            {"organization": "Real Madrid", "scope": "一线队友谊赛、前三场西甲和球场信息", "url": RM_SOURCE, "checkedAt": UPDATED},
            {"organization": "Real Madrid", "scope": "2026/27西甲轮次窗口", "url": LALIGA_SOURCE, "checkedAt": UPDATED},
            {"organization": "UEFA", "scope": "欧冠2026/27资格赛、联赛阶段抽签信息", "url": UEFA_SOURCE, "checkedAt": UPDATED},
            {"organization": "RFEF", "scope": "国王杯、西班牙超级杯官方赛事入口", "url": "https://rfef.es/es/competiciones", "checkedAt": UPDATED},
            {"organization": "LaLiga", "scope": "皇家马德里官方队徽资源来源页面", "url": "https://www.laliga.com/es-GB/clubes/real-madrid/proximos-partidos", "checkedAt": UPDATED},
        ],
        "fixtures": fixtures,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()

import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// public/ 配下の <channel>/<ep>/ をstaticFileで参照する（run.shが配置）
